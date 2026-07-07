from nicegui import ui
import db
from layout import frame

@ui.page('/playgroups')
async def playgroups_page():
    with frame():
        ui.label('Playgroups Management').classes('text-h4 font-bold q-mb-md text-accent')
        
        table_container = ui.column().classes('w-full')
        
        async def load_data():
            table_container.clear()
            records = await db.get_playgroups()
            
            with table_container:
                with ui.row().classes('w-full justify-end q-mb-sm'):
                    ui.button('Add Playgroup', icon='add', on_click=lambda: open_form()).props('color=accent')
                
                columns = [
                    {'name': 'id', 'label': 'ID', 'field': 'id', 'required': True, 'align': 'left'},
                    {'name': 'group_name', 'label': 'Playgroup Name', 'field': 'group_name', 'sortable': True, 'align': 'left'},
                    {'name': 'teacher_name', 'label': 'Teacher', 'field': 'teacher_name', 'sortable': True, 'align': 'left'},
                    {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'},
                ]
                
                table = ui.table(columns=columns, rows=records, row_key='id').classes('w-full premium-card')
                
                table.add_slot('body-cell-actions', '''
                    <q-td :props="props">
                        <q-btn flat dense round color="primary" icon="edit" @click="() => $parent.$emit('edit', props.row)" />
                        <q-btn flat dense round color="negative" icon="delete" @click="() => $parent.$emit('delete', props.row)" />
                    </q-td>
                ''')
                
                table.on('edit', lambda e: open_form(e.args))
                table.on('delete', lambda e: confirm_delete(e.args))

        def open_form(playgroup=None):
            is_edit = playgroup is not None
            
            # Since we need to wait for teachers to load, we define an async func to build the dialog
            async def build_dialog():
                teachers = await db.get_teachers()
                teacher_options = {t['id']: f"{t['first_name']} {t['last_name']}" for t in teachers}
                
                if not teacher_options:
                    ui.notify('You need to add a teacher first!', color='warning')
                    return

                with ui.dialog() as dialog, ui.card().classes('min-w-[400px]'):
                    ui.label('Edit Playgroup' if is_edit else 'Add Playgroup').classes('text-h6 font-bold')
                    
                    group_name = ui.input('Playgroup Name', value=playgroup['group_name'] if is_edit else '').classes('w-full')
                    teacher_select = ui.select(teacher_options, label='Assign Teacher', value=playgroup['teacher_id'] if is_edit else None).classes('w-full')
                    
                    async def save():
                        if not group_name.value or not teacher_select.value:
                            ui.notify('Please fill all fields', color='negative')
                            return
                            
                        if is_edit:
                            await db.update_playgroup(playgroup['id'], group_name.value, teacher_select.value)
                            ui.notify('Playgroup updated', color='positive')
                        else:
                            await db.add_playgroup(group_name.value, teacher_select.value)
                            ui.notify('Playgroup added', color='positive')
                        dialog.close()
                        await load_data()

                    with ui.row().classes('w-full justify-end q-mt-md'):
                        ui.button('Cancel', on_click=dialog.close).props('flat color=grey')
                        ui.button('Save', on_click=save).props('color=primary')
                
                dialog.open()
                
            ui.timer(0, build_dialog, once=True)

        def confirm_delete(playgroup):
            with ui.dialog() as dialog, ui.card():
                ui.label(f"Delete playgroup '{playgroup['group_name']}'?").classes('text-h6')
                ui.label('This will delete all children in this group!').classes('text-negative text-sm q-mt-sm')
                
                async def delete():
                    await db.delete_playgroup(playgroup['id'])
                    ui.notify('Playgroup deleted', color='info')
                    dialog.close()
                    await load_data()

                with ui.row().classes('w-full justify-end q-mt-md'):
                    ui.button('Cancel', on_click=dialog.close).props('flat')
                    ui.button('Delete', on_click=delete).props('color=negative')
            
            dialog.open()

        ui.timer(0, load_data, once=True)
