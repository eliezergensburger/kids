from nicegui import ui
from contextlib import contextmanager

@contextmanager
def frame():
    """Custom page frame to share the same styling and behavior across all pages"""
    
    # Theme configuration
    ui.colors(primary='#1976d2', secondary='#26A69A', accent='#9C27B0', dark='#1d1d1d', positive='#21BA45', negative='#C10015')
    dark_mode = ui.dark_mode()
    
    # Add a custom CSS for premium feel
    ui.add_head_html('''
        <style>
            .premium-card {
                border-radius: 12px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .premium-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            }
            body.body--dark .premium-card {
                box-shadow: 0 4px 6px -1px rgba(255, 255, 255, 0.05), 0 2px 4px -1px rgba(255, 255, 255, 0.03);
                background-color: #2d2d2d;
            }
        </style>
    ''')
    
    with ui.header().classes('items-center justify-between shadow-2'):
        with ui.row().classes('items-center'):
            ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat color=white')
            ui.label('Kids Database Manager').classes('text-h6 font-bold')
        
        with ui.row().classes('items-center gap-4'):
            ui.button(icon='dark_mode', on_click=dark_mode.toggle).props('flat color=white').tooltip('Toggle Dark Mode')
            
    with ui.left_drawer(value=True).classes('bg-blue-grey-1 shadow-2') as left_drawer:
        with ui.column().classes('w-full q-pa-md'):
            ui.label('Navigation').classes('text-overline text-grey-6 q-mb-sm')
            
            with ui.row().classes('w-full hover:bg-grey-3 p-2 rounded cursor-pointer transition-colors').on('click', lambda: ui.navigate.to('/')):
                ui.icon('dashboard', size='sm').classes('text-primary')
                ui.label('Dashboard').classes('ml-2 text-weight-medium')
                
            ui.separator().classes('q-my-sm')
            
            with ui.row().classes('w-full hover:bg-grey-3 p-2 rounded cursor-pointer transition-colors').on('click', lambda: ui.navigate.to('/teachers')):
                ui.icon('school', size='sm').classes('text-secondary')
                ui.label('Teachers').classes('ml-2 text-weight-medium')
                
            with ui.row().classes('w-full hover:bg-grey-3 p-2 rounded cursor-pointer transition-colors').on('click', lambda: ui.navigate.to('/playgroups')):
                ui.icon('groups', size='sm').classes('text-accent')
                ui.label('Playgroups').classes('ml-2 text-weight-medium')
                
            with ui.row().classes('w-full hover:bg-grey-3 p-2 rounded cursor-pointer transition-colors').on('click', lambda: ui.navigate.to('/children')):
                ui.icon('child_care', size='sm').classes('text-positive')
                ui.label('Children').classes('ml-2 text-weight-medium')

    with ui.column().classes('w-full max-w-5xl mx-auto q-pa-md'):
        yield
