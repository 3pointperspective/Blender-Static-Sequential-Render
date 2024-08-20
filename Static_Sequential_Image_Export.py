bl_info = {
    "name": "Static Sequential Image Exporter",
    "blender": (3, 0, 0),
    "category": "Render",
    "description": "Export objects in a collection, using a static camera",
    "location": "View3D > Tool",
}

import bpy
import os
from bpy.props import StringProperty, BoolProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup

class StaticSequenceExporterProperties(PropertyGroup):
    render_collection: StringProperty(
        name="Render Collection",
        description="Select the collection for objects to be rendered",
        default="Objects for Export"
    )
    lighting_collection: StringProperty(
        name="Lighting Collection",
        description="Select the collection for lighting objects",
        default="Lighting"
    )
    output_path: StringProperty(
        name="Output Path",
        description="Select the output path",
        default=r"C:\Users\[user]\Desktop\\",
        subtype='DIR_PATH'
    )
    use_cycles: BoolProperty(
        name="Use Cycles",
        description="Toggle between Eevee and Cycles",
        default=False
    )
    transparent_film: BoolProperty(
        name="Transparent Film",
        description="Toggle between transparent and non-transparent film",
        default=True
    )
    camera_object: PointerProperty(
        name="Camera",
        description="Select the camera object",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'CAMERA'
    )

class STATICSEQUENCE_OT_export(Operator):
    bl_idname = "static_sequence.export"
    bl_label = "Begin Render Sequence"
    
    def execute(self, context):
        props = context.scene.static_sequence_exporter_props
        
        collection_name = props.render_collection
        lighting_collection_name = props.lighting_collection
        output_path = props.output_path
        use_cycles = props.use_cycles
        transparent_film = props.transparent_film
        camera_name = props.camera_object.name if props.camera_object else None
        
        # Set the render engine
        bpy.context.scene.render.engine = 'CYCLES' if use_cycles else 'BLENDER_EEVEE'
        
        # Enable transparency if selected
        bpy.context.scene.render.film_transparent = transparent_film
        
        # Set the camera if provided
        if camera_name:
            bpy.context.scene.camera = bpy.data.objects[camera_name]
        
        # Ensure the output path ends with a slash
        if not output_path.endswith(('/', '\\')):
            output_path += '/'
        
        # Check if the render collection exists
        render_collection = bpy.data.collections.get(collection_name)
        lighting_collection = bpy.data.collections.get(lighting_collection_name)

        if not render_collection:
            self.report({'ERROR'}, f"Collection '{collection_name}' not found.")
            return {'CANCELLED'}
        
        # Check if the output path is valid
        if not os.path.exists(output_path):
            self.report({'ERROR'}, f"Output path '{output_path}' does not exist.")
            return {'CANCELLED'}
        
        # Create a set of all objects in the lighting collection for quick access
        lighting_objs = set(o for o in lighting_collection.objects) if lighting_collection else set()
        
        # Iterate over objects in the render collection
        for obj in render_collection.objects:
            if obj.type == 'MESH':
                # Hide all objects not in the lighting collection
                for other_obj in bpy.context.scene.objects:
                    other_obj.hide_render = other_obj not in lighting_objs and other_obj != obj

                # Ensure the current object is visible
                obj.hide_render = False

                # Update the scene
                bpy.context.view_layer.update()

                # Set the render filepath
                filepath = f'{output_path}{obj.name}.png'
                bpy.context.scene.render.filepath = filepath

                # Render the image
                bpy.ops.render.render(write_still=True)

                # Debug: Confirm rendering
                self.report({'INFO'}, f"Rendered {obj.name} to {filepath}")

        # Restore visibility for all objects
        for obj in bpy.context.scene.objects:
            obj.hide_render = False

        self.report({'INFO'}, "Rendering complete.")
        
        return {'FINISHED'}

class STATICSEQUENCE_PT_export_panel(Panel):
    bl_label = "Static Sequence Exporter"
    bl_idname = "STATICSEQUENCE_PT_export_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Static Sequence Exporter"

    def draw(self, context):
        layout = self.layout
        props = context.scene.static_sequence_exporter_props
        
        layout.prop(props, "render_collection")
        layout.prop(props, "lighting_collection")
        layout.prop(props, "output_path")
        layout.prop(props, "use_cycles")
        layout.prop(props, "transparent_film")
        layout.prop(props, "camera_object")
        
        layout.operator("static_sequence.export", text="Begin Render Sequence")

def register():
    bpy.utils.register_class(StaticSequenceExporterProperties)
    bpy.utils.register_class(STATICSEQUENCE_OT_export)
    bpy.utils.register_class(STATICSEQUENCE_PT_export_panel)
    bpy.types.Scene.static_sequence_exporter_props = PointerProperty(type=StaticSequenceExporterProperties)

def unregister():
    bpy.utils.unregister_class(StaticSequenceExporterProperties)
    bpy.utils.unregister_class(STATICSEQUENCE_OT_export)
    bpy.utils.unregister_class(STATICSEQUENCE_PT_export_panel)
    del bpy.types.Scene.static_sequence_exporter_props

if __name__ == "__main__":
    register()
