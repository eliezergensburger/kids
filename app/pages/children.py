from nicegui import ui
import db
from layout import frame

@ui.page('/children')
async def children_page():
    with frame():
        ui.label('Children Management').classes('text-h4 font-bold q-mb-md text-positive')
        
        table_container = ui.column().classes('w-full')
        
        async def load_data():
            table_container.clear()
            records = await db.get_children()
            
            with table_container:
                with ui.row().classes('w-full justify-end q-mb-sm'):
                    ui.button('Add Child', icon='add', on_click=lambda: open_form()).props('color=positive')
                
                columns = [
                    {'name': 'id', 'label': 'ID', 'field': 'id', 'required': True, 'align': 'left'},
                    {'name': 'first_name', 'label': 'First Name', 'field': 'first_name', 'sortable': True, 'align': 'left'},
                    {'name': 'last_name', 'label': 'Last Name', 'field': 'last_name', 'sortable': True, 'align': 'left'},
                    {'name': 'age', 'label': 'Age', 'field': 'age', 'sortable': True, 'align': 'center'},
                    {'name': 'email', 'label': 'Parent Email', 'field': 'email', 'sortable': True, 'align': 'left'},
                    {'name': 'group_name', 'label': 'Playgroup', 'field': 'group_name', 'sortable': True, 'align': 'left'},
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

        def open_form(child=None):
            is_edit = child is not None
            
            async def build_dialog():
                playgroups = await db.get_playgroups()
                group_options = {p['id']: p['group_name'] for p in playgroups}
                
                if not group_options:
                    ui.notify('You need to add a playgroup first!', color='warning')
                    return

                with ui.dialog() as dialog, ui.card().classes('min-w-[400px]'):
                    ui.label('Edit Child' if is_edit else 'Add Child').classes('text-h6 font-bold')
                    
                    first_name = ui.input('First Name', value=child['first_name'] if is_edit else '').classes('w-full')
                    last_name = ui.input('Last Name', value=child['last_name'] if is_edit else '').classes('w-full')
                    age = ui.number('Age', value=child['age'] if is_edit else 5, format='%.0f').classes('w-full')
                    email = ui.input('Parent Email', value=child['email'] if is_edit else '').classes('w-full')
                    group_select = ui.select(group_options, label='Assign Playgroup', value=child['group_id'] if is_edit else None).classes('w-full')
                    
                    async def save():
                        if not first_name.value or not last_name.value or not age.value or not email.value or not group_select.value:
                            ui.notify('Please fill all fields', color='negative')
                            return
                            
                        if is_edit:
                            await db.update_child(child['id'], first_name.value, last_name.value, int(age.value), email.value, group_select.value)
                            ui.notify('Child updated', color='positive')
                        else:
                            await db.add_child(first_name.value, last_name.value, int(age.value), email.value, group_select.value)
                            ui.notify('Child added', color='positive')
                        dialog.close()
                        await load_data()

                    with ui.row().classes('w-full justify-end q-mt-md'):
                        ui.button('Cancel', on_click=dialog.close).props('flat color=grey')
                        ui.button('Save', on_click=save).props('color=primary')
                
                dialog.open()
                
            ui.timer(0, build_dialog, once=True)

        def confirm_delete(child):
            with ui.dialog() as dialog, ui.card():
                ui.label(f"Delete {child['first_name']} {child['last_name']}?").classes('text-h6')
                
                async def delete():
                    await db.delete_child(child['id'])
                    ui.notify('Child deleted', color='info')
                    dialog.close()
                    await load_data()

                with ui.row().classes('w-full justify-end q-mt-md'):
                    ui.button('Cancel', on_click=dialog.close).props('flat')
                    ui.button('Delete', on_click=delete).props('color=negative')
            
            dialog.open()

        ui.timer(0, load_data, once=True)
