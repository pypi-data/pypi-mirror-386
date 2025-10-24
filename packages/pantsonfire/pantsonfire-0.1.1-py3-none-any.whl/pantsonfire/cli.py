"""Command-line interface for pantsonfire"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
import click

from .factory import create_app
from .models import CheckResult


@click.group()
@click.option('--mode', default='external', help='Operation mode: internal or external')
@click.option('--config', type=click.Path(exists=True), help='Path to config file')
@click.pass_context
def cli(ctx, mode, config):
    """Pantsonfire - Find wrong information in technical docs online"""
    # Store config in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['mode'] = mode
    ctx.obj['config'] = config


@cli.command()
@click.argument('blog_source')
@click.argument('truth_sources', nargs=-1, required=True)
@click.option('--output', '-o', type=click.Path(), help='Output file for results')
@click.option('--format', '-f', default='text', type=click.Choice(['text', 'json', 'csv']),
              help='Output format')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--dry-run', is_flag=True, help='Extract and show content without LLM analysis')
@click.option('--crawl', is_flag=True, help='Enable web crawling to find similar issues')
@click.option('--open-report', is_flag=True, help='Open the analysis report in browser after completion')
@click.pass_context
def check(ctx, blog_source, truth_sources, output, format, verbose, dry_run, crawl, open_report):
    """Check blog content against truth sources for misinformation"""
    try:
        # Create app
        config_overrides = {}
        if dry_run:
            config_overrides["dry_run"] = True
        if ctx.obj.get('config'):
            # Could load config file here if needed
            pass

        app = create_app(mode=ctx.obj['mode'], config=config_overrides)

        if dry_run:
            if verbose:
                click.echo(f"Dry run: Extracting content from {blog_source} and {len(truth_sources)} truth sources...")

            # Extract and show content without LLM analysis
            blog_content = app.extractor.extract(blog_source)
            truth_contents = []

            click.echo(f"\n🔍 BLOG SOURCE: {blog_source}")
            click.echo(f"Content length: {len(blog_content) if blog_content else 0} characters")
            if blog_content and len(blog_content) > 500:
                click.echo(f"Preview: {blog_content[:500]}...")
            elif blog_content:
                click.echo(f"Content: {blog_content}")
            else:
                click.echo("❌ Could not extract content")

            for i, source in enumerate(truth_sources, 1):
                content = app.extractor.extract(source)
                truth_contents.append(content)
                click.echo(f"\n📚 TRUTH SOURCE {i}: {source}")
                click.echo(f"Content length: {len(content) if content else 0} characters")
                if content and len(content) > 300:
                    click.echo(f"Preview: {content[:300]}...")
                elif content:
                    click.echo(f"Content: {content}")
                else:
                    click.echo("❌ Could not extract content")

            return

        if verbose:
            click.echo(f"Checking {blog_source} against {len(truth_sources)} truth sources...")

        # Perform check
        results = app.check_content(blog_source, list(truth_sources))

        if verbose:
            click.echo(f"Results type: {type(results)}")
            if results is not None:
                click.echo(f"Found {len(results)} potential issues")
            else:
                click.echo("Results is None")

        # Display results
        if not results:
            click.echo("No issues detected!")
            return

        # Output to file if specified
        if output:
            output_path = Path(output)
            app.export_logs(output_path, format)
            click.echo(f"Results exported to {output_path}")
        else:
            # Display to console
            _display_results(results, format)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--limit', '-n', type=int, help='Limit number of results to show')
@click.option('--format', '-f', default='text', type=click.Choice(['text', 'json', 'csv']),
              help='Output format')
@click.pass_context
def logs(ctx, limit, format):
    """View stored detection logs"""
    try:
        app = create_app(mode=ctx.obj['mode'])
        results = app.get_logs(limit=limit)

        if not results:
            click.echo("No logs found.")
            return

        _display_results(results, format)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('output_path', type=click.Path())
@click.option('--format', '-f', default='json', type=click.Choice(['json', 'csv', 'text']),
              help='Export format')
@click.option('--limit', '-n', type=int, help='Limit number of results to export')
@click.pass_context
def export(ctx, output_path, format, limit):
    """Export logs to file"""
    try:
        app = create_app(mode=ctx.obj['mode'])
        results = app.get_logs(limit=limit)

        if not results:
            click.echo("No logs to export.")
            return

        output_path = Path(output_path)
        app.export_logs(output_path, format)
        click.echo(f"Exported {len(results)} results to {output_path}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--model', help='LLM model to use (e.g., grok-beta, claude-3-haiku)')
@click.option('--api-key', help='OpenRouter API key (or set OPENROUTER_API_KEY env var)')
@click.option('--test', is_flag=True, help='Test the LLM connection')
@click.pass_context
def config(ctx, model, api_key, test):
    """Configure pantsonfire settings"""
    if api_key:
        os.environ['OPENROUTER_API_KEY'] = api_key
        click.echo("API key set for this session")

    if model:
        click.echo(f"Model preference: {model}")
        click.echo("Note: Model setting is not yet persisted - use config files for now")

    if test:
        try:
            app = create_app(mode=ctx.obj['mode'])
            # Simple test prompt
            test_result = app.llm.client.chat.completions.create(
                model="anthropic/claude-3-haiku",
                messages=[{"role": "user", "content": "Hello, test message"}],
                max_tokens=10
            )
            click.echo("✓ LLM connection successful")
        except Exception as e:
            click.echo(f"✗ LLM connection failed: {e}", err=True)
            sys.exit(1)

    if not any([model, api_key, test]):
        click.echo("Current configuration:")
        click.echo(f"  Mode: {ctx.obj['mode']}")
        click.echo(f"  API Key: {'Set' if os.getenv('OPENROUTER_API_KEY') else 'Not set'}")
        click.echo("  Use --api-key to set API key")
        click.echo("  Use --test to test LLM connection")


def _display_results(results: List[CheckResult], format: str) -> None:
    """Display results in the specified format"""
    if format == 'json':
        import json
        data = [result.to_dict() for result in results]
        click.echo(json.dumps(data, indent=2))

    elif format == 'csv':
        if results:
            click.echo("blog_source,truth_source,discrepancy,confidence,evidence,timestamp")
            for result in results:
                row = [
                    result.blog_source,
                    result.truth_source,
                    result.discrepancy.replace(',', ';'),  # Escape commas
                    f"{result.confidence:.2f}",
                    result.evidence.replace(',', ';'),
                    result.timestamp.isoformat()
                ]
                click.echo(','.join(row))

    else:  # text format
        for i, result in enumerate(results, 1):
            click.echo(f"\n🔥 ISSUE #{i}")
            click.echo(f"Blog: {result.blog_source}")
            click.echo(f"Truth: {result.truth_source}")
            click.echo(f"Confidence: {result.confidence:.2f}")
            click.echo(f"Problem: {result.discrepancy}")
            click.echo(f"Evidence: {result.evidence}")
            click.echo(f"Time: {result.timestamp}")
            if result.tags:
                click.echo(f"Tags: {', '.join(result.tags)}")


@cli.command()
@click.argument('description', nargs=-1)
@click.option('--openrouter', is_flag=True, help='Use OpenRouter for LLM analysis')
@click.option('--crawl', is_flag=True, help='Enable web crawling for broader analysis')
@click.option('--open-report', is_flag=True, help='Open the analysis report in browser after completion')
@click.pass_context
def analyze(ctx, description, openrouter, crawl, open_report):
    """
    Natural language analysis of documentation issues.

    Example: pantsonfire analyze "the oxen website has outdated get early access buttons. find all similar issues on their site"
    """
    try:
        if not description:
            click.echo("❌ Please provide a description of what to analyze.")
            return

        query_text = ' '.join(description)

        # Parse the natural language query
        parsed_info = parse_natural_language_query(query_text)

        if not parsed_info:
            click.echo("❌ Could not parse the analysis request. Please be more specific.")
            return

        print(f"🎯 Analysis Request Parsed:")
        print(f"   Target: {parsed_info.get('target', 'Unknown')}")
        print(f"   Issue: {parsed_info.get('issue', 'Unknown')}")
        print(f"   Sources: {parsed_info.get('sources', [])}")

        # Set up configuration
        config_overrides = {
            "crawl_enabled": crawl,
            "mode": "external"
        }

        if not openrouter:
            config_overrides["dry_run"] = True

        app = create_app(mode="external", config=config_overrides)

        # Initialize analysis in Oxen if using Oxen storage
        if hasattr(app.storage, 'initialize_analysis'):
            analysis_name = parsed_info.get('target', 'unknown').replace(' ', '_').lower()
            if not app.storage.initialize_analysis(analysis_name):
                click.echo("❌ Failed to initialize analysis repository")
                return

        # Extract sources
        sources_to_check = parsed_info.get('sources', [])
        if not sources_to_check:
            click.echo("❌ No sources identified for analysis")
            return

        all_results = []
        crawled_content = {}

        # If crawling is enabled, start with the main sources and crawl for more
        if crawl:
            from ..extractors.web_scraper import WebScraper
            scraper = WebScraper(app.config)

            # Extract keywords from the issue description
            keywords = extract_keywords_from_issue(parsed_info.get('issue', ''))

            # Crawl for similar issues
            crawled_content = scraper.crawl_for_similar_issues(
                sources_to_check,
                keywords,
                max_pages=app.config.crawl_max_pages
            )

            # Analyze crawled content
            crawl_issues = scraper.analyze_found_content(crawled_content, parsed_info.get('issue', ''))
            print(f"🕷️  Found {len(crawl_issues)} potential issues via crawling")

        # Perform analysis on all sources
        all_sources = list(set(sources_to_check + list(crawled_content.keys())))

        for i, source in enumerate(all_sources):
            print(f"🔍 Analyzing source {i+1}/{len(all_sources)}: {source}")

            try:
                # For crawled content, use the content directly
                if source in crawled_content:
                    blog_content = crawled_content[source]
                    truth_sources = [s for s in sources_to_check if s != source]
                else:
                    # Extract content normally
                    blog_content = app.extractor.extract(source)
                    truth_sources = [s for s in all_sources if s != source]

                if not blog_content:
                    print(f"⚠️  Could not extract content from {source}")
                    continue

                # Perform analysis
                results = app.check_content(source, truth_sources)

                if results:
                    all_results.extend(results)
                    print(f"⚠️  Found {len(results)} issues in {source}")
                else:
                    print(f"✅ No issues found in {source}")

            except Exception as e:
                print(f"❌ Error analyzing {source}: {e}")
                continue

        # Store results
        if all_results:
            app.storage.store_findings(all_results)

            # Store extracted content if using Oxen
            if hasattr(app.storage, 'store_extracted_content'):
                content_map = {}
                for source in all_sources:
                    if source in crawled_content:
                        content_map[source] = crawled_content[source]
                    else:
                        extracted = app.extractor.extract(source)
                        if extracted:
                            content_map[source] = extracted

                if content_map:
                    app.storage.store_extracted_content(content_map)

        # Store analysis metadata
        if hasattr(app.storage, 'store_prompts_and_metadata'):
            metadata = {
                "analysis_type": "natural_language",
                "query": query_text,
                "parsed_info": parsed_info,
                "total_sources": len(all_sources),
                "total_findings": len(all_results),
                "crawling_enabled": crawl,
                "llm_used": openrouter,
                "timestamp": datetime.now().isoformat()
            }
            app.storage.store_prompts_and_metadata(metadata)

        # Generate and display report
        print(f"\n📊 ANALYSIS COMPLETE")
        print(f"   Sources analyzed: {len(all_sources)}")
        print(f"   Issues found: {len(all_results)}")
        print(f"   Crawling: {'Enabled' if crawl else 'Disabled'}")
        print(f"   LLM Analysis: {'Enabled' if openrouter else 'Disabled'}")

        if all_results:
            print(f"\n🚨 KEY FINDINGS:")
            for i, result in enumerate(all_results[:5], 1):  # Show first 5
                print(f"   {i}. {result.discrepancy[:100]}...")
                print(f"      Confidence: {result.confidence}")
                print(f"      Source: {result.blog_source}")

            if len(all_results) > 5:
                print(f"   ... and {len(all_results) - 5} more issues")

        # Export local copy for compatibility
        if output:
            app.storage.export_results(all_results, Path(output), format)

        # Open report if requested and Oxen storage is used
        if open_report and hasattr(app.storage, 'open_report_in_browser'):
            app.storage.open_report_in_browser()

        # Show report URL if available
        if hasattr(app.storage, 'generate_report_url'):
            report_url = app.storage.generate_report_url()
            if report_url:
                print(f"\n🔗 Report URL: {report_url}")

    except Exception as e:
        click.echo(f"❌ Analysis failed: {e}")
        raise


def parse_natural_language_query(query: str) -> Optional[Dict]:
    """
    Parse natural language query to extract analysis parameters.

    Args:
        query: Natural language description of analysis

    Returns:
        Dictionary with parsed information or None if parsing fails
    """
    query_lower = query.lower()

    # Extract target (what to analyze)
    targets = []
    if 'oxen' in query_lower:
        targets.append('oxen.ai')
    if 'website' in query_lower or 'site' in query_lower:
        targets.extend(['website', 'webpages'])

    # Extract issue description
    issue_keywords = [
        'outdated', 'wrong', 'incorrect', 'deprecated', 'obsolete',
        'early access', 'get early access', 'coming soon', 'legacy',
        'old', 'broken', 'inaccurate', 'misleading'
    ]

    issue_parts = []
    for keyword in issue_keywords:
        if keyword in query_lower:
            issue_parts.append(keyword)

    # Extract sources from the query
    sources = []
    import re

    # Look for URLs in the query
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, query)
    sources.extend(urls)

    # Look for domain mentions
    if 'oxen.ai' in query_lower:
        if not any('oxen.ai' in url for url in sources):
            sources.extend([
                'https://www.oxen.ai',
                'https://docs.oxen.ai'
            ])

    if not targets:
        targets = ['general']

    return {
        'target': targets[0],
        'issue': ' '.join(issue_parts) if issue_parts else 'general issues',
        'sources': sources,
        'query': query
    }


def extract_keywords_from_issue(issue: str) -> List[str]:
    """Extract keywords from issue description for crawling."""
    keywords = []

    # Common issue keywords
    issue_keywords = [
        'get early access', 'early access', 'coming soon',
        'deprecated', 'outdated', 'legacy', 'obsolete',
        'version', 'update', 'change', 'migration',
        'beta', 'planned', 'removed', 'discontinued'
    ]

    for keyword in issue_keywords:
        if keyword in issue.lower():
            keywords.append(keyword)

    # Add some defaults if none found
    if not keywords:
        keywords = ['deprecated', 'outdated', 'early access']

    return keywords


def main():
    """Entry point for the CLI"""
    cli()


if __name__ == '__main__':
    main()
