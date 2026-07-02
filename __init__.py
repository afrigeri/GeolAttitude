def classFactory(iface):
    from .dip_direction_sampler import DipDirectionSamplerPlugin
    return DipDirectionSamplerPlugin(iface)
