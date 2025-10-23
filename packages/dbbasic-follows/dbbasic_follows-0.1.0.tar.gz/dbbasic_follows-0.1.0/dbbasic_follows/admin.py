"""
Admin interface configuration for dbbasic-follows

This module is auto-discovered by dbbasic-admin.
"""

# Navigation configuration
# This is automatically discovered and added to the admin menu
ADMIN_CONFIG = [
    {
        'icon': '👥',  # Social graph / people icon
        'label': 'Follows',
        'href': '/admin/follows',
        'order': 40  # Position in menu
    }
]
