#support for icons
#based on enthought example icons.py and icons_view.enaml

from os.path import dirname, join
from enaml.image_provider import Image
from enaml.icon_provider import IconProvider, Icon, IconImage

ROOT = join(dirname(__file__), 'icons')

class CsIconProvider(IconProvider):
    path_map = {
        '/plus': 'plus.png',
        '/minus': 'minus.png',
        '/atom_loading':'atom_loading.png'
    }

    def request_icon(self, path, callback):
        """ Load the requested icon.

        Parameters
        ----------
        path : str
            The requested path of the icon, with the provider prefix
            removed. For example, if the full icon source path was:
            'icon://myicons/window-icon' then the path passed to this
            method will be `/window-icon`.

        callback : callable
            A callable which should be invoked when the icon is loaded.
            It accepts a single argument, which is the loaded `Icon`
            object. It is safe to invoke this callable from a thread.

        """
        pth = self.path_map.get(path)
        if pth is not None:
            with open(join(ROOT, pth), 'rb') as f:
                data = f.read()
            image = Image(data=data)
            icon_img = IconImage(image=image)
            icon = Icon(images=[icon_img])
        else:
            icon = None
        callback(icon)