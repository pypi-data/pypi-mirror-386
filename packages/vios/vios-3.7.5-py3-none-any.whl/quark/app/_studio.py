# MIT License

# Copyright (c) 2021 YL Feng

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import random
import time
from datetime import datetime
from importlib import reload
from pathlib import Path

import h5py
import matplotlib.image as mim
import matplotlib.pyplot as plt
import numpy as np
from srpc import loads

from ._db import get_record_list_by_name, get_record_set_by_name


def query(app: str = None, start: datetime = None, end: datetime = None, page: int = 1) -> tuple:
    """query records from database

    Args:
        app (str, optional): task name. Defaults to None.
        start (datetime, optional): start time. Defaults to None.
        end (datetime, optional): end time. Defaults to None.
        page (int, optional): page number. Defaults to 1.

    Returns:
        tuple: header, table content, pages, task names
    """
    print(app, start, end, page)
    if not app:
        return [], [], [r[0] for r in get_record_set_by_name()]
    records = get_record_list_by_name(app, start.strftime(
        '%Y-%m-%d-%H-%M-%S'), end.strftime('%Y-%m-%d-%H-%M-%S'))
    headers = ['id', 'tid', 'name', 'user', 'priority', 'system', 'status',
               'filename', 'dataset', 'created', 'finished', 'committed']
    return headers, records[::-1], {}


def update(rid: int, tags: str):
    pass


def load(rid: int):
    from . import get_data_by_rid
    from ._viewer import fig

    data = get_data_by_rid(rid, plot=True, backend=False)
    return data

    fig.clear(backend='')

    axes = fig.subplot(3)
    axes[0].imshow(np.random.randn(30, 20),
                   xdata=np.arange(30) * 1e6,
                   ydata=np.arange(20),
                   colormap='jet',
                   title='image')

    axes[1].plot(np.random.randn(100),
                 xdata=np.arange(100),
                 linestyle='-.',
                 linecolor='b',
                 markersize=5,
                 xlabel='xx',
                 ylabel='yyy')
    axes[1].plot(np.random.randn(100) + 10,
                 xdata=np.arange(100),
                 title='curve')

    axes[2].scatter(np.random.randn(100),
                    xdata=np.arange(100),
                    markercolor='b',
                    markersize=10)
    axes[2].scatter(np.random.randn(100),
                    xdata=np.arange(100),
                    markercolor='r',
                    markersize=5,
                    title='scatter')

    return fig.data


def history(path: str = 'Q0.Spectrum') -> np.ndarray:
    try:
        import run
        run = reload(run)
        return run.get_history_data(path)
    except Exception as e:
        with open(Path.home() / 'Desktop/home/cfg/dag.json', 'r') as f:
            dag = loads(f.read())
            node, method = path.split('.')
            return np.array(dag[node][method]['history'])[:, -1].astype(float)
        return np.random.randn(101)


def digraph(node: str = 'Q0') -> dict:
    try:
        import run
        run = reload(run)
        return run.get_task_graph(node)
    except Exception as e:
        return {'nodes': {'s21': {'pos': (3, 1)},  # , 'pen': (135, 155, 75, 255, 5)
                          'Spectrum': {'pos': (3, 3)},
                          'Rabi': {'pos': (3, 5)},
                          'Ramsey': {'pos': (1, 8)},
                          'Scatter': {'pos': (5, 8)},
                          'RB': {'pos': (3, 10)}},

                'edges': {('s21', 'Spectrum'): {'name': ''},  # , 'pen': (155, 123, 255, 180, 2)
                          ('Spectrum', 'Rabi'): {'name': ''},
                          ('Rabi', 'Ramsey'): {'name': ''},
                          ('Rabi', 'Scatter'): {'name': ''},
                          ('Scatter', 'RB'): {'name': ''}}}


def tpgraph():
    try:
        import run
        run = reload(run)
        return run.get_chip_graph()
    except Exception as e:
        layout = {'nodes': {}, 'edges': {}}

        for i in range(72):
            row, col = divmod(i, 6)
            layout['nodes'][f'Q{i}'] = {
                # must be tuple
                'label': f'Q{i}',
                'pos': (1 * (2 * col + row % 2), 1 * (22 - row)),
                'pen': (235, 155, 75, 255, 1),
                'value': {'a': {'b': 0, 'c': 0, 'd': 0, 'e': 0, 'f': 0}}
            }

        for i in range(121):
            row, col = divmod(i, 11)
            if col % 2 == 0:
                layout['edges'][(f'Q{row * 6 + col // 2}', f'Q{row * 6 + col // 2 + 6}')] = {
                    'label': f'C{i}',
                    'pen': (35, 155, 75, 255, 48),
                    'value': {'a': {'b': 0, 'c': 0, 'd': 0, 'e': 0, 'f': 0}}
                }
            elif col % 2 == 1 and row % 2 == 0:
                layout['edges'][(f'Q{row * 6 + col // 2 + 1}', f'Q{row * 6 + col // 2 + 6}')] = {
                    'label': f'C{i}',
                    'pen': (35, 155, 75, 255, 48),
                    'value': {'a': {'b': 0, 'c': 0, 'd': 0, 'e': 0, 'f': 0}}
                }
            elif col % 2 == 1 and row % 2 == 1:
                layout['edges'][(f'Q{row * 6 + col // 2}', f'Q{row * 6 + col // 2 + 7}')] = {
                    'label': f'C{i}',
                    'pen': (35, 155, 75, 255, 48),
                    'value': {'a': {'b': 0, 'c': 0, 'd': 0, 'e': 0, 'f': 0}}
                }
            return layout


def totable(data: dict):
    '''dict to table
    '''
    try:
        import run
        run = reload(run)
        headers, table = run.dict_to_table(data)
    except Exception as e:
        print(e)
        headers = ['a', 'b.c', 'c.d.e']
        table = [[f"Name {i}", i, f"City {i % 10}"] for i in range(500)]

    return headers, table

# region plot


def mplot(fig, data):

    axes = fig.subplots(nrows=8, ncols=4)

    # 为每个子图添加内容
    for i in range(8):
        for j in range(4):
            ax = axes[i, j]
            x = np.linspace(0, 2 * np.pi, 100)
            y = np.sin(x + (i * 4 + j) * 0.5)
            ax.plot(x, y)
            ax.set_title(f'Plot {i * 4 + j + 1}')
            ax.grid(True)

    return

    ax = fig.add_subplot(1, 1, 1)
    # ax.plot(np.random.randn(1024), '-o')
    # First create the x and y coordinates of the points.
    n_angles = 36
    n_radii = 8
    min_radius = 0.25
    radii = np.linspace(min_radius, 0.95, n_radii)

    angles = np.linspace(0, 2 * np.pi, n_angles, endpoint=False)
    angles = np.repeat(angles[..., np.newaxis], n_radii, axis=1)
    angles[:, 1::2] += np.pi / n_angles

    x = (radii * np.cos(angles)).flatten()
    y = (radii * np.sin(angles)).flatten()

    # Create the Triangulation; no triangles so Delaunay triangulation created.
    import matplotlib.tri as tri
    triang = tri.Triangulation(x, y)

    # Mask off unwanted triangles.
    triang.set_mask(np.hypot(x[triang.triangles].mean(axis=1),
                             y[triang.triangles].mean(axis=1))
                    < min_radius)

    ax.set_aspect('equal')
    ax.triplot(triang, 'bo-', lw=1)
    ax.set_title('triplot of Delaunay triangulation')
    return 3000, 3000


def demo(fig):
    # demo: read image file
    # img = np.rot90(mim.imread(
    #     Path(__file__).parents[2]/'tests/test/mac.png'), 2)
    # img = np.moveaxis(img, [0, -1], [-1, 0])
    # fig.layer({'name': 'example of image', 'zdata': img})

    # demo: show image from array
    fig.layer(
        {'name': 'example of image[array]', 'zdata': np.random.randn(5, 101, 201)})

    # demo: plot layer by layer
    tlist = np.arange(-2 * np.pi, 2 * np.pi, 0.05)
    for i in range(8):
        fig.layer(dict(name=f'example of layer plot[{i}]',
                       ydata=np.random.random(
                           1) * np.sin(2 * np.pi * 0.707 * tlist) / tlist,
                       xdata=tlist,
                       title='vcplot',
                       legend='scatter',
                       clear=False,
                       marker=random.choice(
                           ['o', 's', 't', 'd', '+', 'x', 'p', 'h', 'star']),
                       markercolor='r',
                       markersize=12,
                       xlabel='this is xlabel',
                       ylabel='this is ylabel',
                       xunits='xunits',
                       yunits='yunits'))
        fig.layer(dict(name=f'example of layer plot[{i}]',
                       ydata=np.random.random(
                           1) * 2 * np.sin(2 * np.pi * 0.707 * tlist) / tlist,
                       xdata=tlist))
    # demo: subplot like matplotlib
    axes = fig.subplot(4, 4)
    for ax in axes[::2]:
        cmap = random.choice(plt.colormaps())
        # ax.imshow(img[0, :, :], colormap=cmap, title=cmap)
    for ax in axes[1::2]:
        ax.plot(np.sin(2 * np.pi * 0.707 * tlist) / tlist,
                title='vcplot',
                xdata=tlist,
                marker=random.choice(
                    ['o', 's', 't', 'd', '+', 'x', 'p', 'h', 'star']),
                markercolor=random.choice(
                    ['r', 'g', 'b', 'k', 'c', 'm', 'y', (255, 0, 255)]),
                linestyle=random.choice(
            ['-', '.', '--', '-.', '-..', 'none']),
            linecolor=random.choice(
                    ['r', 'g', 'b', 'k', 'c', 'm', 'y', (31, 119, 180)]))


def qplot(fig, dataset: list[str]):
    print('ptype', dataset)

    filename, dsname = dataset

    if filename.endswith('hdf5'):
        with h5py.File(filename) as f:
            ds = f[dsname]
            info = loads(dict(ds.parent.attrs).get('snapshot', '{}'))
            shape = info['meta']['other']['shape']
            data = ds[:].reshape(*shape, 2)
    print(info, data)
    return  # demo(fig)

    data, meta = dataset
    cfg = loads(meta)
    data = np.asarray(data)

    name = cfg['meta']['arguments'].get('name', 'None')
    print(cfg['meta']['index'].keys(), data.shape)

    qubits = cfg['meta']['arguments'].get('qubits', 'None')

    axes = fig.subplot(2, 2)
    for i, qubit in enumerate(qubits):
        freq = cfg['meta']['index']['time']
        res = data[:, i]

        sf = freq[np.argmin(np.abs(res))]
        # print(sf)
        axes[i].plot(np.abs(res),
                     title=qubit,
                     xdata=freq,
                     legend=str(sf),
                     marker='o',
                     markercolor='b',
                     linestyle='-.',
                     linecolor=random.choice(
            ['r', 'g', 'b', 'k', 'c', 'm', 'y', (31, 119, 180)]))

# endregion plot
