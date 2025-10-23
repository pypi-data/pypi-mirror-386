"""
Hook commands for Voice Mode - primarily for Claude Code integration.
"""

import click
import sys
import json
import os
from pathlib import Path
from typing import Optional


@click.group()
@click.help_option('-h', '--help', help='Show this message and exit')
def hooks():
    """Manage Voice Mode hooks and event handlers."""
    pass


@hooks.command('receiver')
@click.option('--tool-name', help='Override tool name (for testing)')
@click.option('--action', type=click.Choice(['start', 'end']), help='Override action (for testing)')
@click.option('--subagent-type', help='Override subagent type (for testing)')
@click.option('--event', type=click.Choice(['PreToolUse', 'PostToolUse']), help='Override event (for testing)')
@click.option('--debug', is_flag=True, help='Enable debug output')
def receiver(tool_name, action, subagent_type, event, debug):
    """Receive and process hook events from Claude Code via stdin.
    
    This command reads JSON from stdin when called by Claude Code hooks,
    or accepts command-line arguments for testing.
    
    The filesystem structure defines sound mappings:
    ~/.voicemode/soundfonts/current/PreToolUse/task/subagent/baby-bear.wav
    
    Examples:
        # Called by Claude Code (reads JSON from stdin)
        voicemode claude hooks receiver
        
        # Testing with defaults
        voicemode claude hooks receiver --debug
        
        # Testing with specific values
        voicemode claude hooks receiver --tool-name Task --action start --subagent-type mama-bear
    """
    from voice_mode.tools.sound_fonts.audio_player import Player
    
    # Try to read JSON from stdin if available
    hook_data = {}
    if not sys.stdin.isatty():
        try:
            hook_data = json.load(sys.stdin)
            if debug:
                print(f"[DEBUG] Received JSON: {json.dumps(hook_data, indent=2)}", file=sys.stderr)
        except Exception as e:
            if debug:
                print(f"[DEBUG] Failed to parse JSON from stdin: {e}", file=sys.stderr)
            # Silent fail for hooks
            sys.exit(0)
    
    # Extract values from JSON or use command-line overrides/defaults
    if not tool_name:
        tool_name = hook_data.get('tool_name', 'Task')
    
    if not event:
        event_name = hook_data.get('hook_event_name', 'PreToolUse')
    else:
        event_name = event
    
    # Map event to action if not specified
    if not action:
        if event_name == 'PreToolUse':
            action = 'start'
        elif event_name == 'PostToolUse':
            action = 'end'
        else:
            action = 'start'  # Default
    
    # Get subagent_type from tool_input if not specified
    if not subagent_type and tool_name == 'Task':
        tool_input = hook_data.get('tool_input', {})
        subagent_type = tool_input.get('subagent_type', 'baby-bear')
    elif not subagent_type:
        subagent_type = None
    
    if debug:
        print(f"[DEBUG] Processing: event={event_name}, tool={tool_name}, "
              f"action={action}, subagent={subagent_type}", file=sys.stderr)
    
    # Check if sound fonts are enabled
    from voice_mode.config import SOUNDFONTS_ENABLED
    
    if not SOUNDFONTS_ENABLED:
        if debug:
            print(f"[DEBUG] Sound fonts are disabled (VOICEMODE_SOUNDFONTS_ENABLED=false)", file=sys.stderr)
    else:
        # Find sound file using filesystem conventions
        sound_file = find_sound_file(event_name, tool_name, subagent_type)
        
        if sound_file:
            if debug:
                print(f"[DEBUG] Found sound file: {sound_file}", file=sys.stderr)
            
            # Play the sound
            player = Player()
            success = player.play(str(sound_file))
            
            if debug:
                if success:
                    print(f"[DEBUG] Sound played successfully", file=sys.stderr)
                else:
                    print(f"[DEBUG] Failed to play sound", file=sys.stderr)
        else:
            if debug:
                print(f"[DEBUG] No sound file found for this event", file=sys.stderr)
    
    # Always exit 0 to not disrupt Claude Code
    sys.exit(0)


def find_sound_file(event: str, tool: str, subagent: Optional[str] = None) -> Optional[Path]:
    """
    Find sound file using filesystem conventions.
    
    Tries paths in order (mp3 preferred over wav for size):
    1. Most specific: {event}/{tool}/subagent/{subagent}.{mp3,wav} (Task tool only)
    2. Tool default: {event}/{tool}/default.{mp3,wav}
    3. Event default: {event}/default.{mp3,wav}
    4. Global fallback: fallback.{mp3,wav}
    
    Args:
        event: Event name (PreToolUse, PostToolUse)
        tool: Tool name (lowercase)
        subagent: Optional subagent type (lowercase)
        
    Returns:
        Path to sound file if found, None otherwise
    """
    # Get base path (follow symlink if exists)
    base_path = Path.home() / '.voicemode' / 'soundfonts' / 'current'
    
    # Resolve symlink if it exists
    if base_path.is_symlink():
        base_path = base_path.resolve()
    
    if not base_path.exists():
        return None
    
    # Normalize names to lowercase for filesystem
    event = event.lower() if event else 'pretooluse'
    tool = tool.lower() if tool else 'default'
    subagent = subagent.lower() if subagent else None
    
    # Map event names to directory names
    event_map = {
        'pretooluse': 'PreToolUse',
        'posttooluse': 'PostToolUse',
        'start': 'PreToolUse',
        'end': 'PostToolUse'
    }
    event_dir = event_map.get(event, event)
    
    # Build list of paths to try (most specific to least specific)
    paths_to_try = []
    
    # 1. Most specific: subagent sound (Task tool only)
    if tool == 'task' and subagent:
        # Try mp3 first (smaller), then wav
        paths_to_try.append(base_path / event_dir / tool / 'subagent' / f'{subagent}.mp3')
        paths_to_try.append(base_path / event_dir / tool / 'subagent' / f'{subagent}.wav')
    
    # 2. Tool-specific default
    paths_to_try.append(base_path / event_dir / tool / 'default.mp3')
    paths_to_try.append(base_path / event_dir / tool / 'default.wav')
    
    # 3. Event-level default
    paths_to_try.append(base_path / event_dir / 'default.mp3')
    paths_to_try.append(base_path / event_dir / 'default.wav')
    
    # 4. Global fallback
    paths_to_try.append(base_path / 'fallback.mp3')
    paths_to_try.append(base_path / 'fallback.wav')
    
    # Find first existing file
    for path in paths_to_try:
        if path.exists():
            return path
    
    return None


# Keep the old stdin-receiver command for backwards compatibility (deprecated)
@hooks.command('stdin-receiver', hidden=True)
@click.argument('tool_name')
@click.argument('action', type=click.Choice(['start', 'end', 'complete']))
@click.argument('subagent_type', required=False)
@click.option('--debug', is_flag=True, help='Enable debug output')
def stdin_receiver_deprecated(tool_name, action, subagent_type, event, debug):
    """[DEPRECATED] Use receiver instead."""
    # Call the new receiver command
    ctx = click.get_current_context()
    ctx.invoke(receiver, 
               tool_name=tool_name,
               action=action,
               subagent_type=subagent_type,
               event=event,
               debug=debug)