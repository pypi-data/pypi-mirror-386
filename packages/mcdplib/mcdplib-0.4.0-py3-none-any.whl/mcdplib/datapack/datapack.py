from mcdplib.core.file import extensions_file_selector
from mcdplib.core.registry import Registry, RegistryResourceType, RegistryResourceBuilderLoader
from mcdplib.core.pack import PackInformation, PackFeatures, PackFilters, PackOverlays, Pack
from mcdplib.core.resource.resource_binary import BinaryResource, StaticBinaryResourceBuilderLoader
from mcdplib.core.resource.resource_string import StringResource, StaticStringResourceBuilderLoader
from mcdplib.datapack.function import FunctionResourceBuilderLoader
from mcdplib.datapack.function_template import FunctionTemplateResourceBuilderLoader


class Datapack(Pack):
    DATA_DIRECTORY: str = "data"

    def __init__(self, information: PackInformation, features: PackFeatures | None = None, filters: PackFilters | None = None, overlays: PackOverlays | None = None, icon: bytes | None = None):
        super().__init__(information, Datapack.DATA_DIRECTORY, features, filters, overlays, icon)

        self.functions: Registry = Registry(
            name="function",
            resource_types=[RegistryResourceType(
                resource_types=[StringResource],
                file_extension="mcfunction"
            )],
            resource_builder_loaders=[
                RegistryResourceBuilderLoader(
                    file_selector=extensions_file_selector(["mcfunction"]),
                    resource_builder_loader=StaticStringResourceBuilderLoader()
                ),
                RegistryResourceBuilderLoader(
                    file_selector=extensions_file_selector(["mcf"]),
                    resource_builder_loader=FunctionResourceBuilderLoader()
                ),
                RegistryResourceBuilderLoader(
                    file_selector=extensions_file_selector(["mcft"]),
                    resource_builder_loader=FunctionTemplateResourceBuilderLoader()
                )
            ]
        )
        self.add_registry(self.functions)

        self.structures: Registry = Registry(
            name="structure",
            resource_types=[RegistryResourceType(
                resource_types=[BinaryResource],
                file_extension="nbt"
            )],
            resource_builder_loaders=[RegistryResourceBuilderLoader(
                file_selector=extensions_file_selector(["nbt"]),
                resource_builder_loader=StaticBinaryResourceBuilderLoader()
            )]
        )
        self.add_registry(self.structures)

        self.banner_pattern_tags: Registry = self._create_object_resource_registry("tags/banner_pattern")
        self.block_tags: Registry = self._create_object_resource_registry("tags/block")
        self.damage_type_tags: Registry = self._create_object_resource_registry("tags/damage_type")
        self.dialog_tags: Registry = self._create_object_resource_registry("tags/dialog")
        self.enchantment_tags: Registry = self._create_object_resource_registry("tags/enchantment")
        self.entity_type_tags: Registry = self._create_object_resource_registry("tags/entity_type")
        self.fluid_tags: Registry = self._create_object_resource_registry("tags/fluid")
        self.function_tags: Registry = self._create_object_resource_registry("tags/function")
        self.game_event_tags: Registry = self._create_object_resource_registry("tags/game_event")
        self.instrument_tags: Registry = self._create_object_resource_registry("tags/instrument")
        self.item_tags: Registry = self._create_object_resource_registry("tags/item")
        self.painting_variant_tags: Registry = self._create_object_resource_registry("tags/painting_variant")
        self.point_of_interest_type_tags: Registry = self._create_object_resource_registry("tags/point_of_interest_type")
        self.worldgen_biome_tags: Registry = self._create_object_resource_registry("tags/worldgen/biome")
        self.worldgen_flat_level_generator_preset_tags: Registry = self._create_object_resource_registry("tags/worldgen/flat_level_generator_preset")
        self.worldgen_structure_tags: Registry = self._create_object_resource_registry("tags/worldgen/structure")
        self.worldgen_world_preset_tags: Registry = self._create_object_resource_registry("tags/worldgen/world_preset")

        self.advancements: Registry = self._create_object_resource_registry("advancement")
        self.banner_patterns: Registry = self._create_object_resource_registry("banner_pattern")
        self.cat_variants: Registry = self._create_object_resource_registry("cat_variant")
        self.chat_types: Registry = self._create_object_resource_registry("chat_type")
        self.chicken_variants: Registry = self._create_object_resource_registry("chicken_variant")
        self.cow_variants: Registry = self._create_object_resource_registry("cow_variant")
        self.damage_types: Registry = self._create_object_resource_registry("damage_type")
        self.dialogs: Registry = self._create_object_resource_registry("dialog")
        self.dimensions: Registry = self._create_object_resource_registry("dimension")
        self.dimension_types: Registry = self._create_object_resource_registry("dimension_type")
        self.enchantments: Registry = self._create_object_resource_registry("enchantment")
        self.enchantment_providers: Registry = self._create_object_resource_registry("enchantment_provider")
        self.frog_variants: Registry = self._create_object_resource_registry("frog_variant")
        self.instruments: Registry = self._create_object_resource_registry("instrument")
        self.item_modifiers: Registry = self._create_object_resource_registry("item_modifier")
        self.jukebox_songs: Registry = self._create_object_resource_registry("jukebox_song")
        self.loot_tables: Registry = self._create_object_resource_registry("loot_table")
        self.painting_variants: Registry = self._create_object_resource_registry("painting_variant")
        self.pig_variants: Registry = self._create_object_resource_registry("pig_variant")
        self.predicates: Registry = self._create_object_resource_registry("predicate")
        self.recipes: Registry = self._create_object_resource_registry("recipe")
        self.test_environments: Registry = self._create_object_resource_registry("test_environment")
        self.test_instances: Registry = self._create_object_resource_registry("test_instance")
        self.trial_spawners: Registry = self._create_object_resource_registry("trial_spawner")
        self.trim_materials: Registry = self._create_object_resource_registry("trim_material")
        self.trim_patterns: Registry = self._create_object_resource_registry("trim_pattern")
        self.wolf_sound_variants: Registry = self._create_object_resource_registry("wolf_sound_variant")
        self.wolf_variants: Registry = self._create_object_resource_registry("wolf_variant")

        self.worldgen_biomes: Registry = self._create_object_resource_registry("worldgen/biome")
        self.worldgen_configured_carvers: Registry = self._create_object_resource_registry("worldgen/configured_carver")
        self.worldgen_configured_features: Registry = self._create_object_resource_registry("worldgen/configured_feature")
        self.worldgen_density_functions: Registry = self._create_object_resource_registry("worldgen/density_function")
        self.worldgen_noises: Registry = self._create_object_resource_registry("worldgen/noise")
        self.worldgen_noise_settings: Registry = self._create_object_resource_registry("worldgen/noise_settings")
        self.worldgen_placed_features: Registry = self._create_object_resource_registry("worldgen/placed_feature")
        self.worldgen_processor_lists: Registry = self._create_object_resource_registry("worldgen/processor_list")
        self.worldgen_structures: Registry = self._create_object_resource_registry("worldgen/structure")
        self.worldgen_structure_sets: Registry = self._create_object_resource_registry("worldgen/structure_set")
        self.worldgen_template_pools: Registry = self._create_object_resource_registry("worldgen/template_pool")
        self.worldgen_world_presets: Registry = self._create_object_resource_registry("worldgen/world_preset")
        self.worldgen_flat_level_generator_presets: Registry = self._create_object_resource_registry("worldgen/flat_level_generator_preset")
        self.worldgen_multi_noise_biome_source_parameter_lists: Registry = self._create_object_resource_registry("worldgen/multi_noise_biome_source_parameter_list")
