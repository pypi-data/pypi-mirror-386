"""Main exporter module for Discord chat export"""

from pathlib import Path
from typing import List
import html as html_module

try:
    import discord
except ImportError:
    pass


async def export_chat(channel, limit: int = 100, output_file: str = None) -> str:
    """
    Export Discord channel messages to HTML
    
    Args:
        channel: Discord channel object (TextChannel, Thread, etc.)
        limit: Maximum number of messages to export (default: 100)
        output_file: Path to save HTML file (default: channel_name.html)
    
    Returns:
        Path to the generated HTML file
    """
    if output_file is None:
        output_file = f"{channel.name}.html"
    
    # Fetch messages
    messages = []
    async for message in channel.history(limit=limit, oldest_first=True):
        messages.append(message)
    
    # Generate HTML
    html_content = _generate_html(channel, messages)
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_file


def _generate_html(channel, messages: List) -> str:
    """Generate HTML content from messages"""
    
    # Get template path
    template_path = Path(__file__).parent / "template.html"
    
    # Read template
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Generate messages HTML
    messages_html = ""
    for msg in messages:
        messages_html += _format_message(msg)
    
    # Replace placeholders
    html_content = template.replace("{{CHANNEL_NAME}}", html_module.escape(channel.name))
    html_content = html_content.replace("{{MESSAGES}}", messages_html)
    
    # Add guild name if available
    guild_name = channel.guild.name if hasattr(channel, 'guild') and channel.guild else "Direct Message"
    html_content = html_content.replace("{{GUILD_NAME}}", html_module.escape(guild_name))
    
    return html_content


def _format_message(message) -> str:
    """Format a single message as HTML"""
    
    # Format timestamp
    timestamp = message.created_at.strftime("%d.%m.%Y %H:%M")
    
    # Get avatar URL
    avatar_url = message.author.display_avatar.url if message.author.display_avatar else ""
    
    # Escape HTML in content
    content = html_module.escape(message.content) if message.content else ""
    
    # Replace newlines with <br>
    content = content.replace("\n", "<br>")
    
    # Get author name and color
    author_name = html_module.escape(message.author.display_name)
    author_color = "#ffffff"
    
    # Try to get role color
    if hasattr(message.author, 'color') and message.author.color.value != 0:
        author_color = f"#{message.author.color.value:06x}"
    
    # Handle attachments
    attachments_html = ""
    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith('image'):
                attachments_html += f'<img src="{attachment.url}" class="attachment-image" alt="attachment">'
            else:
                attachments_html += f'<a href="{attachment.url}" class="attachment-link" target="_blank">📎 {html_module.escape(attachment.filename)}</a>'
    
    # Handle embeds
    embeds_html = ""
    if message.embeds:
        for embed in message.embeds:
            embed_color = f"#{embed.color.value:06x}" if embed.color else "#202225"
            embed_title = html_module.escape(embed.title) if embed.title else ""
            embed_description = html_module.escape(embed.description) if embed.description else ""
            
            embeds_html += f'''
            <div class="embed" style="border-left-color: {embed_color};">
                {f'<div class="embed-title">{embed_title}</div>' if embed_title else ''}
                {f'<div class="embed-description">{embed_description}</div>' if embed_description else ''}
            </div>
            '''
    
    message_html = f'''
    <div class="message">
        <img src="{avatar_url}" class="avatar" alt="avatar">
        <div class="message-content">
            <div class="message-header">
                <span class="author-name" style="color: {author_color};">{author_name}</span>
                <span class="timestamp">{timestamp}</span>
            </div>
            <div class="message-text">{content}</div>
            {attachments_html}
            {embeds_html}
        </div>
    </div>
    '''
    
    return message_html