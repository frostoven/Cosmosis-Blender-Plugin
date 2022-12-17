import bpy

bl_info = {
    "name": "CosmosisDev",
    "blender": (2, 80, 0),
    "category": "Object",
}

# This is the dropdown that contains all mesh types.
mesh_code_types = []

# All menu items are disabled by default. This informs the menu builder
# which items should be visible for the given mesh code type.
code_menu_items = {}

# Used to load mesh properties into the plugin.
allowed_external_keys = [
    'csmType', 'csmModuleHook', 'csmGfxqLight'
]

# --- Mesh type definitions --- #

mesh_code_types.append(('csmUndefined', 'Not set', ''))
code_menu_items['csmUndefined'] = []

mesh_code_types.append(('csmAreaLight', 'Area light', ''))
code_menu_items['csmAreaLight'] = ['csmModuleHook', 'csmGfxqLight']


# --- Add-on object --- #

class ObjectCosmosisObjectProperties(bpy.types.Operator):
    """Cosmosis Object Properties"""
    bl_idname = 'object.cosmosis_object_properties'
    bl_label = 'Cosmosis Object Properties'
    bl_options = {'REGISTER', 'UNDO'}
    has_initialized = False

    # --- Optional menu items section --- #

    # int example: bpy.props.IntProperty(name="", default=2, min=1, max=100)

    csmModuleHook: bpy.props.StringProperty(
        name="[Module hook]",
        description="Optional; examples: cockpitLights | externalLights"
    )

    csmGfxqLight: bpy.props.EnumProperty(
        name="[Lighting quality]",
        description="Used to prevent the light from rendering on certain GFX "
                    "quality settings",
        items=(
            ('auto', 'Engine decides', ''),
            ('low', 'Only render if low quality', ''),
            ('low,medium', 'Only render if medium or lower quality', ''),
            ('medium', 'Only render if medium quality', ''),
            ('medium,high', 'Only render if medium or higher quality', ''),
            ('high', 'Only render if high quality', ''),
        )
    )

    # --- Optional menu items section end --- #

    csmType: bpy.props.EnumProperty(
        name='Mesh type',
        items=mesh_code_types
    )

    def execute(self, context):
        # On first run, read all object properties and save them here.
        if not self.has_initialized:
            self.has_initialized = True
            for key in allowed_external_keys:
                try:
                    # Filthy hack, but could not find a cleaner way of doing
                    # this.
                    expression = 'if context.object["' + key + '"]: ' + \
                                 'self.' + key + \
                                 ' = context.object["' + key + '"] \n' + \
                                 'else: self.' + key + ' = ""'
                    exec(expression)
                except KeyError:
                    pass

        # Set object properties to the user-chosen type
        if self.csmType == 'csmUndefined' and 'csmType' in context.object:
            del context.object['csmType']
        elif self.csmType:
            for key in ['csmType'] + code_menu_items[self.csmType]:
                try:
                    # Filthy hack, but could not find a cleaner way of doing
                    # this.
                    expression = 'if self.' + key + ' != "": ' + \
                                 'context.object["' + key + '"]' + \
                                 ' = self.' + key
                    exec(expression)
                except KeyError:
                    pass

        return {'FINISHED'}

    def draw(self, _context):
        layout = self.layout
        layout.use_property_split = True
        # Always dray type by default.
        layout.prop(self, 'csmType')

        active_type = self.csmType
        menu_items = code_menu_items[active_type]
        if len(menu_items) > 0:
            layout.label(text='Preferences')

        # Only draw menu items relevant to the selected type.
        for menu_item in menu_items:
            if menu_item == 'csmType':
                # Disallow drawing type a second time.
                continue
            # Draw the menu item.
            layout.prop(self, menu_item)

    @staticmethod
    def alert_info(message):
        bpy.context.window_manager.popup_menu(
            ObjectCosmosisObjectProperties.draw_modal,
            title=message, icon="INFO"
        )

    @staticmethod
    def alert_error(message):
        bpy.context.window_manager.popup_menu(
            ObjectCosmosisObjectProperties.draw_modal,
            title=message, icon="ERROR"
        )

    @staticmethod
    def draw_modal(self, context):
        pass


def menu_func(self, _context):
    self.layout.operator(ObjectCosmosisObjectProperties.bl_idname)


# store keymaps here to access after registration
addon_keymaps = []


def register():
    bpy.utils.register_class(ObjectCosmosisObjectProperties)
    bpy.types.VIEW3D_MT_object.append(menu_func)

    # handle the keymap
    wm = bpy.context.window_manager
    # Note that in background mode (no GUI available), keyconfigs are not
    # available either, so we have to check this to avoid nasty errors in
    # background case.
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode',
                                             space_type='EMPTY')
        kmi = km.keymap_items.new(ObjectCosmosisObjectProperties.bl_idname,
                                  'INSERT', 'PRESS', ctrl=False, shift=False)

        # Note: anything that does not have a default value defined here will
        # inherit the value of whatever previous object you had selected. This
        # old value will then actively be injected into the new object if it
        # does not have that value already defined.
        kmi.properties.csmType = 'csmUndefined'
        kmi.properties.csmModuleHook = ''
        kmi.properties.csmGfxqLight = 'auto'
        addon_keymaps.append((km, kmi))


def unregister():
    # Note: when unregistering, it's usually good practice to do it in
    # reverse order you registered. Can avoid strange issues like keymap
    # still referring to operators already unregistered... handle the keymap
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.utils.unregister_class(ObjectCosmosisObjectProperties)
    bpy.types.VIEW3D_MT_object.remove(menu_func)


if __name__ == '__main__':
    register()
