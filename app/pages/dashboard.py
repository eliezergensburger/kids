from nicegui import ui
import pandas as pd
import db
from layout import frame

@ui.page('/')
async def dashboard():
    with frame():
        ui.label('Dashboard Overview').classes('text-h4 font-bold q-mb-md text-primary')
        
        # Fetch data for dashboard
        teachers = await db.get_teachers()
        playgroups = await db.get_playgroups()
        children = await db.get_children()
        
        # KPI Cards
        with ui.row().classes('w-full gap-4 q-mb-xl justify-between'):
            with ui.card().classes('premium-card col grow text-center q-pa-md'):
                ui.icon('school', size='xl').classes('text-secondary q-mb-sm')
                ui.label(str(len(teachers))).classes('text-h3 font-bold')
                ui.label('Total Teachers').classes('text-subtitle1 text-grey-6')
                
            with ui.card().classes('premium-card col grow text-center q-pa-md'):
                ui.icon('groups', size='xl').classes('text-accent q-mb-sm')
                ui.label(str(len(playgroups))).classes('text-h3 font-bold')
                ui.label('Total Playgroups').classes('text-subtitle1 text-grey-6')
                
            with ui.card().classes('premium-card col grow text-center q-pa-md'):
                ui.icon('child_care', size='xl').classes('text-positive q-mb-sm')
                ui.label(str(len(children))).classes('text-h3 font-bold')
                ui.label('Total Children').classes('text-subtitle1 text-grey-6')

        if not children:
            ui.label('No data available for graphs.').classes('text-italic text-grey')
            return

        df_children = pd.DataFrame(children)
        
        # Graphs
        with ui.row().classes('w-full gap-8'):
            # Bar Chart: Children per Playgroup
            with ui.card().classes('premium-card col grow q-pa-md'):
                ui.label('Children per Playgroup').classes('text-h6 font-bold q-mb-md')
                group_counts = df_children['group_name'].value_counts().reset_index()
                group_counts.columns = ['Playgroup', 'Count']
                
                import plotly.express as px
                fig_bar = px.bar(group_counts, x='Playgroup', y='Count', 
                                 color='Playgroup', 
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_bar.update_layout(margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)")
                ui.plotly(fig_bar).classes('w-full h-64')

            # Pie Chart: Age Distribution
            with ui.card().classes('premium-card col grow q-pa-md'):
                ui.label('Age Distribution').classes('text-h6 font-bold q-mb-md')
                age_counts = df_children['age'].value_counts().reset_index()
                age_counts.columns = ['Age', 'Count']
                
                fig_pie = px.pie(age_counts, values='Count', names='Age', hole=0.4,
                                 color_discrete_sequence=px.colors.qualitative.Set3)
                fig_pie.update_layout(margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)")
                ui.plotly(fig_pie).classes('w-full h-64')
