def sidebar_color(request):
    # Default color scheme (Sky)
    color_scheme = request.session.get('color_scheme', 'sky')
    
    color_palettes = {
        'sky': {
            'sidebar_bg_from': 'from-sky-800',
            'sidebar_bg_to': 'to-sky-900',
            'menu_text': 'text-white',
            'menu_hover_bg': 'hover:bg-white/10',
            'menu_icon_bg': 'bg-white/10',
            'border_color': 'border-white/10',
            'active_class': 'bg-white/20',
            'active_text': 'text-white',
            'name': 'Sky Blue'
        },
        'emerald': {
            'sidebar_bg_from': 'from-emerald-700',
            'sidebar_bg_to': 'to-emerald-900',
            'menu_text': 'text-white',
            'menu_hover_bg': 'hover:bg-white/10',
            'menu_icon_bg': 'bg-white/10',
            'border_color': 'border-white/10',
            'active_class': 'bg-white/20',
            'active_text': 'text-white',
            'name': 'Emerald Green'
        },
        'purple': {
            'sidebar_bg_from': 'from-purple-800',
            'sidebar_bg_to': 'to-purple-900',
            'menu_text': 'text-white',
            'menu_hover_bg': 'hover:bg-white/10',
            'menu_icon_bg': 'bg-white/10',
            'border_color': 'border-white/10',
            'active_class': 'bg-white/20',
            'active_text': 'text-white',
            'name': 'Deep Purple'
        },
        'indigo': {
            'sidebar_bg_from': 'from-indigo-800',
            'sidebar_bg_to': 'to-indigo-900',
            'menu_text': 'text-white',
            'menu_hover_bg': 'hover:bg-white/10',
            'menu_icon_bg': 'bg-white/10',
            'border_color': 'border-white/10',
            'active_class': 'bg-white/20',
            'active_text': 'text-white',
            'name': 'Royal Indigo'
        },
        'slate': {
            'sidebar_bg_from': 'from-slate-800',
            'sidebar_bg_to': 'to-slate-900',
            'menu_text': 'text-white',
            'menu_hover_bg': 'hover:bg-white/10',
            'menu_icon_bg': 'bg-white/10',
            'border_color': 'border-white/10',
            'active_class': 'bg-white/20',
            'active_text': 'text-white',
            'name': 'Dark Slate'
        },
        'light': {
            'sidebar_bg_from': 'from-gray-50',
            'sidebar_bg_to': 'to-gray-100',
            'menu_text': 'text-gray-700',
            'menu_hover_bg': 'hover:bg-gray-200',
            'menu_icon_bg': 'bg-gray-200',
            'border_color': 'border-gray-200',
            'active_class': 'bg-blue-100',
            'active_text': 'text-blue-700',
            'name': 'Light Mode'
        }
    }
    
    return {
        'sidebar_colors': color_palettes[color_scheme],
        'color_schemes': color_palettes
    }