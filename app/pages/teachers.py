from nicegui import ui
import db
from layout import frame

@ui.page('/teachers')
async def teachers_page():
    with frame():
        ui.label('Teachers Management').classes('text-h4 font-bold q-mb-md text-secondary')
        
        # Container for the table so we can refresh it
        table_container = ui.column().classes('w-full')
        
        async def load_data():
            table_container.clear()
            records = await db.get_teachers()
            
            with table_container:
                with ui.row().classes('w-full justify-end q-mb-sm'):
                    ui.button('Add Teacher', icon='add', on_click=lambda: open_form()).props('color=secondary')
                
                columns = [
                    {'name': 'id', 'label': 'ID', 'field': 'id', 'required': True, 'align': 'left'},
                    {'name': 'first_name', 'label': 'First Name', 'field': 'first_name', 'sortable': True, 'align': 'left'},
                    {'name': 'last_name', 'label': 'Last Name', 'field': 'last_name', 'sortable': True, 'align': 'left'},
                    {'name': 'email', 'label': 'Email', 'field': 'email', 'sortable': True, 'align': 'left'},
                    {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'},
                ]
                
                table = ui.table(columns=columns, rows=records, row_key='id').classes('w-full premium-card')
                
                # Custom cell rendering for actions
                table.add_slot('body-cell-actions', '''
                    <q-td :props="props">
                        <q-btn flat dense round color="primary" icon="edit" @click="() => $parent.$emit('edit', props.row)" />
                        <q-btn flat dense round color="negative" icon="delete" @click="() => $parent.$emit('delete', props.row)" />
                    </q-td>
                ''')
                
                # Event handlers for table actions
                table.on('edit', lambda e: open_form(e.args))
                table.on('delete', lambda e: confirm_delete(e.args))

        def open_form(teacher=None):
            is_edit = teacher is not None
            with ui.dialog() as dialog, ui.card().classes('min-w-[400px]'):
                ui.label('Edit Teacher' if is_edit else 'Add Teacher').classes('text-h6 font-bold')
                first_name = ui.input('First Name', value=teacher['first_name'] if is_edit else '').classes('w-full')
                last_name = ui.input('Last Name', value=teacher['last_name'] if is_edit else '').classes('w-full')
                email = ui.input('Email', value=teacher['email'] if is_edit else '').classes('w-full')
                
                async def save():
                    if not first_name.value or not last_name.value or not email.value:
                        ui.notify('Please fill all fields', color='negative')
                        return
                        
                    if is_edit:
                        await db.update_teacher(teacher['id'], first_name.value, last_name.value, email.value)
                        ui.notify('Teacher updated', color='positive')
                    else:
                        await db.add_teacher(first_name.value, last_name.value, email.value)
                        ui.notify('Teacher added', color='positive')
                    dialog.close()
                    await load_data()

                with ui.row().classes('w-full justify-end q-mt-md'):
                    ui.button('Cancel', on_click=dialog.close).props('flat color=grey')
                    ui.button('Save', on_click=save).props('color=primary')
            
            dialog.open()

        def confirm_delete(teacher):
            with ui.dialog() as dialog, ui.card():
                ui.label(f"Are you sure you want to delete {teacher['first_name']} {teacher['last_name']}?").classes('text-h6')
                ui.label('This will also delete any playgroups assigned to this teacher!').classes('text-negative text-sm q-mt-sm')
                
                async def delete():
                    await db.delete_teacher(teacher['id'])
                    ui.notify('Teacher deleted', color='info')
                    dialog.close()
                    await load_data()

                with ui.row().classes('w-full justify-end q-mt-md'):
                    ui.button('Cancel', on_click=dialog.close).props('flat')
                    ui.button('Delete', on_click=delete).props('color=negative')
            
            dialog.open()

        # Initial load
        ui.timer(0, load_data, once=True)
