import numpy as np

# define InteractionType
class InteractionType:
    DOOR_OPEN = "door_open"
    DOOR_CLOSE = "door_close"
    DRAWER_OPEN = "drawer_open"
    DRAWER_CLOSE = "drawer_close"
    WINDOW_OPEN = "window_open"
    WINDOW_CLOSE = "window_close"
    SWITCH_ON = "switch_on"
    SWITCH_OFF = "switch_off"
    BUTTON_PRESS = "button_press"
    LEVER_PULL = "lever_pull"
    KNOB_TURN = "knob_turn"

class Scene:
    def __init__(self, objects=None):
        if objects is not None:
            self.objects = objects
        else:
            try:
                import bpy
                self.objects = list(bpy.context.scene.objects)
            except (ImportError, AttributeError):
                self.objects = []
    
    def __getstate__(self):
        """Return state for pickle serialization"""
        # Only serialize object names and basic attributes, not the actual Blender objects
        serializable_objects = []
        for obj in self.objects:
            try:
                # Create a serializable representation of the object
                obj_info = {
                    'name': obj.name,
                    'type': obj.type if hasattr(obj, 'type') else None,
                    'location': list(obj.location) if hasattr(obj, 'location') else [0, 0, 0],
                    'dimensions': list(obj.dimensions) if hasattr(obj, 'dimensions') else [1, 1, 1],
                }
                # Add custom properties if they exist
                if hasattr(obj, 'get'):
                    for key in ['category', 'is_interactive']:
                        value = obj.get(key, None)
                        if value is not None:
                            obj_info[key] = value
                serializable_objects.append(obj_info)
            except Exception:
                # Skip objects that can't be serialized
                continue
        return {'objects': serializable_objects}
    
    def __setstate__(self, state):
        """Restore state from pickle deserialization"""
        self.objects = state.get('objects', [])

    def get_categories(self):
        """Returns a sorted list of unique category names present in the scene."""
        categories = set()
        for obj in self.objects:
            # Handle both Blender objects and serialized object representations
            if isinstance(obj, dict):
                # Serialized object representation
                obj_name = obj.get('name', '')
                category = obj.get('category', None)
            else:
                # Blender object
                obj_name = obj.name
                category = obj.get("category", None) if hasattr(obj, 'get') else None

            # Attempt to derive category from the factory name, which is more specific
            if '(' in obj_name and 'Factory' in obj_name:
                try:
                    factory_name = obj_name.split('(')[0]
                    if factory_name.endswith('Factory'):
                        category = factory_name[:-7]  # Remove 'Factory'
                        categories.add(category)
                        continue
                except Exception:
                    pass

            # Fallback to the original method if the name doesn't match the pattern
            if category is not None:
                categories.add(category)
        return sorted(categories)

    def get_category_count(self):
        """Computes the number of unique categories in the scene."""
        return len(self.get_categories())
    
    def get_instance_count(self):
        result = len(self.objects)
        return result

    def get_interactive_category_ratio(self):
        interactive_cats = []
        for obj in self.objects:
            # Handle both Blender objects and serialized object representations
            if isinstance(obj, dict):
                # Serialized object representation
                is_interactive = obj.get("is_interactive", False)
                category = obj.get("category", None)
            else:
                # Blender object
                is_interactive = obj.get("is_interactive", False) if hasattr(obj, 'get') else False
                category = obj.get("category", None) if hasattr(obj, 'get') else None
            
            if is_interactive and category is not None:
                interactive_cats.append(category)
        return len(set(interactive_cats)) / max(1, self.get_category_count())

    def get_floor_area(self):
        """Return the total floor area of the indoor scene.

        Strategy:
        - When running inside Blender, sum the areas of faces tagged as
          support surfaces on objects tagged as rooms. This uses the
          tagging system to isolate floor faces and polygon areas for
          precise measurement, with a fallback to extracting the tagged
          faces and computing area via a helper.
        - Outside Blender (or when tags are unavailable), approximate by
          summing footprint areas for serialized objects whose names hint
          they represent rooms/floors using their X-Y dimensions.
        """
        total_floor_area = 0.0

        # Attempt Blender and tagging imports
        blender_available = False
        tagging_available = False
        try:
            import bpy  # type: ignore
            from mathutils import Vector # type: ignore
            blender_available = True
        except ImportError:
            blender_available = False

        if blender_available:
            try:
                from infinigen.core import tags as t  # type: ignore
                from infinigen.core import tagging  # type: ignore
                from infinigen.core.util import blender as butil  # type: ignore
                tagging_available = True
            except Exception:
                tagging_available = False

        if blender_available and tagging_available:
            for obj in self.objects:
                # Skip non-Blender objects
                if isinstance(obj, dict) or not hasattr(obj, 'type'):
                    continue # Only real scene objects has attribute "type"
                #State Objects and Factory Objects do not have attribute "type"

                try:
                    if obj.type != "MESH" or not hasattr(obj, "data"):
                        continue

                    # Consider any mesh that is not explicitly an "object" as potential room geometry
                    obj_tags = tagging.union_object_tags(obj)
                    if obj_tags and t.Semantics.Object in obj_tags:
                        continue
                    
                    # Build a face mask for floor (support) faces
                    try:
                        face_mask = tagging.tagged_face_mask(
                            obj, {t.Subpart.SupportSurface}
                        )
                    except Exception:
                        face_mask = None

                    if face_mask is not None and hasattr(obj.data, "polygons"):
                        face_area_sum = 0.0
                        up = Vector((0.0, 0.0, 1.0))
                        
                        polys = obj.data.polygons
                        if len(polys) == len(face_mask):
                            for p, is_support in zip(polys, face_mask):
                                if is_support:
                                    # Ensure the face is horizontal and facing up
                                    normal = butil.global_polygon_normal(obj, p)
                                    if normal.dot(up) > 0.95: # Check if normal is close to vertical
                                        face_area_sum += p.area
                            total_floor_area += face_area_sum
                                
                except Exception:
                    # Skip any object that fails processing
                    continue

            return total_floor_area

        # Fallback for serialized/non-Blender contexts: approximate footprint
        for obj in self.objects:
            if not isinstance(obj, dict):
                continue
            try:
                name = str(obj.get("name", "")).lower()
                dims = obj.get("dimensions", None)
                if not dims or len(dims) < 2:
                    continue
                # Heuristic: treat objects with 'room' or 'floor' in name as floor shells
                if ("room" in name) or ("floor" in name):
                    x, y = float(dims[0]), float(dims[1])
                    total_floor_area += abs(x * y)
            except Exception:
                continue

        return total_floor_area

    def get_surface_area(self):
        """Return the total surface area of all objects in the scene.

        Preference order per object:
        1) Use custom property 'area' if present and positive
        2) If in Blender and object is a mesh, compute using precise face areas
           (via core.util.blender.surface_area or mesh polygon areas)
        3) Fallback: approximate via the object's bounding box dimensions

        Handles both Blender objects and serialized dictionaries.
        """
        try:
            import bpy  # type: ignore
            blender_available = True
        except ImportError:
            blender_available = False

        # Try to import the helper for precise mesh surface area
        compute_surface_area = None
        if blender_available:
            try:
                from infinigen.core.util.blender import surface_area as _surface_area  # type: ignore
                compute_surface_area = _surface_area
            except Exception:
                compute_surface_area = None

        def bbox_surface_area_from_dims(dims):
            try:
                x, y, z = float(dims[0]), float(dims[1]), float(dims[2])
                return 2.0 * (abs(x * y) + abs(y * z) + abs(z * x))
            except Exception:
                return 0.0

        total_area = 0.0

        for obj in self.objects:
            # Serialized object path
            if isinstance(obj, dict):
                try:
                    area_val = obj.get("area", None)
                    if isinstance(area_val, (int, float)) and area_val > 0:
                        total_area += float(area_val)
                        continue

                    dims = obj.get("dimensions", None)
                    if dims is not None and len(dims) >= 3:
                        total_area += bbox_surface_area_from_dims(dims)
                except Exception:
                    pass
                continue

            # Blender object path
            try:
                # 1) Precomputed custom property
                custom_area = obj.get("area", None) if hasattr(obj, "get") else None
                if isinstance(custom_area, (int, float)) and custom_area > 0:
                    total_area += float(custom_area)
                    continue

                # 2) Geometry-based computation if possible
                if blender_available and getattr(obj, "type", None) == "MESH" and hasattr(obj, "data"):
                    area_val = None
                    if compute_surface_area is not None:
                        try:
                            area_val = float(compute_surface_area(obj))
                        except Exception:
                            area_val = None

                    if area_val is None:
                        mesh = obj.data
                        if hasattr(mesh, "polygons"):
                            try:
                                if hasattr(mesh, "calc_area"):
                                    mesh.calc_area()
                                area_val = float(sum(p.area for p in mesh.polygons))
                            except Exception:
                                area_val = None

                    if area_val is not None:
                        total_area += area_val
                        continue

                # 3) Fallback: bounding box approximation
                if hasattr(obj, "dimensions"):
                    total_area += bbox_surface_area_from_dims(obj.dimensions)
            except Exception:
                # Skip unprocessable objects
                continue

        return total_area
    
    def get_interactive_category_ratio(self):
        interactive_cats = []
        for obj in self.objects:
            if obj.get("is_interactive", False):
                category = obj.get("category", None)
                if category is not None:
                    interactive_cats.append(category)
        return len(set(interactive_cats)) / max(1, self.get_category_count())

    def get_object_density(self, floor_area = None):
        # self.objects: get the total number of all objects in the scene
        return len(self.objects) / max(1e-4, floor_area)

    def get_spatial_entropy(self):
        # Use Shannon Entropy to measure spatial distribution
        positions = []
        for obj in self.objects:
            if isinstance(obj, dict):
                # Serialized object representation
                location = obj.get('location', [0, 0, 0])
            else:
                # Blender object
                location = obj.location if hasattr(obj, 'location') else [0, 0, 0]
            positions.append(location)
        
        if len(positions) < 2:
            return 0
        
        positions = np.array(positions)
        hist, _ = np.histogramdd(positions, bins=(5,5,1))
        p = hist.flatten()/hist.sum()
        p = p[p>0]
        entropy = -np.sum(p*np.log(p))
        max_entropy = np.log(len(p))  # max possible entropy
        return entropy/max_entropy if max_entropy > 0 else 0

    def get_interactive_object_density(self, floor_area = None):
        """Computes the density of interactive objects per unit floor area."""
        interactive_count = 0
        for obj in self.objects:
            if isinstance(obj, dict):
                # Serialized object representation
                is_interactive = obj.get("is_interactive", False)
            else:
                # Blender object
                is_interactive = obj.get("is_interactive", False) if hasattr(obj, 'get') else False
            if is_interactive:
                interactive_count += 1
        return interactive_count / max(1e-4, floor_area)

    def get_interactive_object_proportion(self):
        """Computes the proportion of interactive instances in the scene."""
        if not self.objects:
            return 0.0
        interactive_count = 0
        for obj in self.objects:
            if isinstance(obj, dict):
                # Serialized object representation
                is_interactive = obj.get("is_interactive", False)
            else:
                # Blender object
                is_interactive = obj.get("is_interactive", False) if hasattr(obj, 'get') else False
            if is_interactive:
                interactive_count += 1
        return interactive_count / len(self.objects)

    def get_interaction_type_count(self):
        """Computes the number of unique interaction types in the scene."""
        interaction_types = set()
        for obj in self.objects:
            if isinstance(obj, dict):
                # Serialized object representation
                obj_interaction_types = obj.get("interaction_types", [])
            else:
                # Blender object
                obj_interaction_types = obj.get("interaction_types", []) if hasattr(obj, 'get') else []
            if obj_interaction_types:
                interaction_types.update(obj_interaction_types)
        return len(interaction_types)


    def get_material_count(self):
        """Calculates the number of unique material types in the scene."""
        unique_material_types = set()
        for obj in self.objects:
            if isinstance(obj, dict):
                # Serialized object representation - skip material counting for now
                continue
            else:
                # Blender object
                if hasattr(obj, 'material_slots'):
                    for slot in obj.material_slots:
                        if slot.material and slot.material.name:
                            # Extract the base name of the material 
                            # (e.g., 'shader_plaster' from 'shader_plaster.047')
                            base_name = slot.material.name.split('.')[0]
                            unique_material_types.add(base_name)
        
        import logging
        logging.info(f"Unique material types in scene: {sorted(list(unique_material_types))}")
        return len(unique_material_types)


    def get_avg_poly_count(self):
        """Computes the average polygon count of objects in the scene that have polygons."""
        try:
            import bpy
            blender_available = True
        except ImportError:
            blender_available = False
            
        if not blender_available:
            return 0
            
        poly_counts = []
        for obj in self.objects:
            if isinstance(obj, dict):
                # Serialized object representation - skip poly count for now
                continue
            else:
                # Blender object
                # first try to read poly_count from custom properties
                poly_count = obj.get("poly_count", None) if hasattr(obj, 'get') else None
                
                # if no custom properties, then calculate it
                if poly_count is None:
                    if (hasattr(obj, 'data') and
                        hasattr(obj.data, 'polygons') and
                        obj.type == "MESH"):
                        poly_count = len(obj.data.polygons)
                    else:
                        poly_count = 0
                
                if poly_count > 0:  # only count objects with polygons
                    poly_counts.append(poly_count)
        
        return np.mean(poly_counts) if poly_counts else 0

