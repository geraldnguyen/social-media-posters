#!/usr/bin/env python3
"""
CLI wrapper for social media posting scripts.
Provides unified command-line interface for all post-to-XYZ scripts.
"""

import sys
import os
from pathlib import Path
import click

# Add parent directory to path to import common utilities and post scripts
sys.path.insert(0, str(Path(__file__).parent.parent))

from social_cli import __version__


def set_env_from_option(ctx, param, value):
    """Set environment variable from click option."""
    if value is not None:
        env_var = param.name.upper().replace('-', '_')
        os.environ[env_var] = str(value)
    return value


def set_boolean_env_from_flag(ctx, param, value):
    """Set environment variable from boolean flag."""
    if value:
        env_var = param.name.upper().replace('-', '_')
        os.environ[env_var] = 'true'
    return value


# Common options used across multiple commands
common_options = [
    click.option('--dry-run', is_flag=True, callback=set_boolean_env_from_flag, 
                 help='Run in dry-run mode without posting'),
    click.option('--input-file', callback=set_env_from_option, 
                 help='Path to JSON input file'),
    click.option('--content-json', callback=set_env_from_option, 
                 help='URL to JSON data for templating'),
    click.option('--log-level', callback=set_env_from_option, 
                 help='Logging level (DEBUG, INFO, WARNING, ERROR)'),
    click.option('--post-content', callback=set_env_from_option, 
                 help='Content to post'),
    click.option('--media-files', callback=set_env_from_option, 
                 help='Comma-separated list of media files or URLs'),
    click.option('--max-download-size-mb', callback=set_env_from_option, type=int,
                 help='Maximum size for remote media downloads (MB)'),
]


def add_common_options(func):
    """Decorator to add common options to commands."""
    for option in reversed(common_options):
        func = option(func)
    return func


@click.group()
@click.version_option(version=__version__, prog_name='social')
def main():
    """Social media posting CLI tool.
    
    Post content to various social media platforms from the command line.
    Supports X (Twitter), Facebook, Instagram, Threads, LinkedIn, YouTube, and Bluesky.
    """
    pass


@main.command()
@add_common_options
@click.option('--x-api-key', callback=set_env_from_option, 
              help='X API key')
@click.option('--x-api-secret', callback=set_env_from_option, 
              help='X API secret')
@click.option('--x-access-token', callback=set_env_from_option, 
              help='X access token')
@click.option('--x-access-token-secret', callback=set_env_from_option, 
              help='X access token secret')
def x(**kwargs):
    """Post to X (formerly Twitter)."""
    # Import from post-to-x folder
    sys.path.insert(0, str(Path(__file__).parent.parent / 'post-to-x'))
    from post_to_x import post_to_x as post_func
    try:
        post_func()
    except SystemExit as e:
        sys.exit(e.code)


@main.command()
@add_common_options
@click.option('--fb-page-id', callback=set_env_from_option, 
              help='Facebook Page ID')
@click.option('--fb-access-token', callback=set_env_from_option, 
              help='Facebook Page access token')
@click.option('--post-link', callback=set_env_from_option, 
              help='Link to attach to the post')
@click.option('--post-privacy', callback=set_env_from_option, 
              help='Post privacy (public or private)')
def facebook(**kwargs):
    """Post to Facebook Page."""
    # Import from post-to-facebook folder
    sys.path.insert(0, str(Path(__file__).parent.parent / 'post-to-facebook'))
    from post_to_facebook import post_to_facebook as post_func
    try:
        post_func()
    except SystemExit as e:
        sys.exit(e.code)


@main.command()
@add_common_options
@click.option('--ig-user-id', callback=set_env_from_option, 
              help='Instagram user ID')
@click.option('--ig-access-token', callback=set_env_from_option, 
              help='Instagram access token')
@click.option('--media-file', callback=set_env_from_option, 
              help='Single media file URL (deprecated, use --media-files)')
def instagram(**kwargs):
    """Post to Instagram."""
    # Import from post-to-instagram folder
    sys.path.insert(0, str(Path(__file__).parent.parent / 'post-to-instagram'))
    from post_to_instagram import post_to_instagram as post_func
    try:
        post_func()
    except SystemExit as e:
        sys.exit(e.code)


@main.command()
@add_common_options
@click.option('--threads-user-id', callback=set_env_from_option, 
              help='Threads user ID')
@click.option('--threads-access-token', callback=set_env_from_option, 
              help='Threads access token')
@click.option('--post-link', callback=set_env_from_option, 
              help='Link to attach to the post')
@click.option('--media-file', callback=set_env_from_option, 
              help='Single media file URL (deprecated, use --media-files)')
def threads(**kwargs):
    """Post to Threads."""
    # Import from post-to-threads folder
    sys.path.insert(0, str(Path(__file__).parent.parent / 'post-to-threads'))
    from post_to_threads import post_to_threads as post_func
    try:
        post_func()
    except SystemExit as e:
        sys.exit(e.code)


@main.command()
@add_common_options
@click.option('--linkedin-access-token', callback=set_env_from_option, 
              help='LinkedIn access token')
@click.option('--linkedin-author-id', callback=set_env_from_option, 
              help='LinkedIn author ID (person or organization URN)')
@click.option('--post-link', callback=set_env_from_option, 
              help='Link to attach to the post')
def linkedin(**kwargs):
    """Post to LinkedIn."""
    # Import from post-to-linkedin folder
    sys.path.insert(0, str(Path(__file__).parent.parent / 'post-to-linkedin'))
    from post_to_linkedin import post_to_linkedin as post_func
    try:
        post_func()
    except SystemExit as e:
        sys.exit(e.code)


@main.command()
@add_common_options
@click.option('--bluesky-identifier', callback=set_env_from_option, 
              help='Bluesky identifier (username or email)')
@click.option('--bluesky-password', callback=set_env_from_option, 
              help='Bluesky password')
@click.option('--post-link', callback=set_env_from_option, 
              help='Link to attach to the post')
def bluesky(**kwargs):
    """Post to Bluesky."""
    # Import from post-to-bluesky folder
    sys.path.insert(0, str(Path(__file__).parent.parent / 'post-to-bluesky'))
    from post_to_bluesky import post_to_bluesky as post_func
    try:
        post_func()
    except SystemExit as e:
        sys.exit(e.code)


@main.command()
@add_common_options
@click.option('--youtube-api-key', callback=set_env_from_option, 
              help='YouTube API key (credentials JSON)')
@click.option('--youtube-oauth-client-id', callback=set_env_from_option, 
              help='YouTube OAuth client ID')
@click.option('--youtube-oauth-client-secret', callback=set_env_from_option, 
              help='YouTube OAuth client secret')
@click.option('--youtube-oauth-refresh-token', callback=set_env_from_option, 
              help='YouTube OAuth refresh token')
@click.option('--youtube-oauth-scopes', callback=set_env_from_option, 
              help='YouTube OAuth scopes (comma-separated)')
@click.option('--video-file', callback=set_env_from_option, 
              help='Path or URL to video file')
@click.option('--video-title', callback=set_env_from_option, 
              help='Video title')
@click.option('--video-description', callback=set_env_from_option, 
              help='Video description')
@click.option('--video-tags', callback=set_env_from_option, 
              help='Video tags (comma-separated)')
@click.option('--video-category-id', callback=set_env_from_option, 
              help='Video category ID')
@click.option('--video-privacy-status', callback=set_env_from_option, 
              help='Video privacy status (public, private, unlisted)')
@click.option('--video-publish-at', callback=set_env_from_option, 
              help='Schedule publish date/time (ISO 8601 format)')
@click.option('--video-made-for-kids', callback=set_env_from_option, 
              help='Video is made for kids (true/false)')
@click.option('--video-embeddable', callback=set_env_from_option, 
              help='Video is embeddable (true/false)')
@click.option('--video-license', callback=set_env_from_option, 
              help='Video license (youtube or creativeCommon)')
@click.option('--video-public-stats-viewable', callback=set_env_from_option, 
              help='Public stats viewable (true/false)')
@click.option('--video-contains-synthetic-media', callback=set_env_from_option, 
              help='Video contains synthetic media (true/false)')
@click.option('--video-thumbnail', callback=set_env_from_option, 
              help='Path to custom thumbnail')
@click.option('--playlist-id', callback=set_env_from_option, 
              help='Playlist ID to add video to')
def youtube(**kwargs):
    """Upload video to YouTube."""
    # Import from post-to-youtube folder
    sys.path.insert(0, str(Path(__file__).parent.parent / 'post-to-youtube'))
    from post_to_youtube import post_to_youtube as post_func
    try:
        post_func()
    except SystemExit as e:
        sys.exit(e.code)


if __name__ == '__main__':
    main()
