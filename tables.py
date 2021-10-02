from flask_table import Table, Col, LinkCol
 
class Results(Table):
    user_id = Col('Id', show=False)
    user_name = Col('Name')
    form_number = Col('Form')
    case_number = Col('Case')
    case_status = Col('Status')
    form_description = Col('Description')
    user_password = Col('Password', show=False)
    edit = LinkCol('Edit', 'edit_view', url_kwargs=dict(id='user_id'))
    delete = LinkCol('Delete', 'delete_user', url_kwargs=dict(id='user_id'))