def find_action_from_menu(menu, action_name):
    """
    Verify if an action (a conversion unit) is available in a context menu.

    Parameters
    ----------
    menu : QMenu
        The context menu of a widget
    action_name : str
        A menu text item

    Returns
    -------
    True if the action name is found in the menu; False otherwise
    """
    for action in menu.actions():
        if action.menu():
            # The action will always contain a menu, so the status will be created
            status = find_action_from_menu(action.menu(), action_name)
        if not action.isSeparator():
            if action_name == action.text():
                return True
    return status
