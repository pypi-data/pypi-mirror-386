import os
import numpy as np
import figctx as ctx
import pytest

testdata = np.random.rand(2,100)

def test(tmp_path):

    save_to1 = tmp_path / 'test1.png'
    save_to2 = tmp_path / 'test2.png'
    save_to3 = tmp_path / 'test3.png'
    save_to4 = tmp_path / 'test4.png'

    with ctx.single(80, 60, save_to1) as (fig,ax):
        
        ax.plot(testdata[0], testdata[1])
        ax.set_title('ax title')

        fig.suptitle('fig title')
    
    with ctx.single(160, 60, save_to2, 2, 1) as (fig, ax):

        c = ax[0]

        c.errorbar(testdata[0], testdata[1], fmt='-o')

        c = ax[1]

        c.scatter(testdata[1], testdata[0], label='Testlabel')

        c.legend()

    with ctx.multi(70, 150, 1, 1, [1], [1], save_to3) as (fig, subfig):

        c = subfig[0]
        
        ax = c.subplots(1,1)
        ax.tick_params(
                direction='in',
                width=1,
                length=3,
                pad=2
            )
        ax.plot(testdata[0], 2*testdata[1], label='Test1')
        ax.legend()
        ax.set_title('ax title1')

    with ctx.multi(70, 150, 2, 1, [1], [1,2], save_to4) as (fig, subfig):

        c = subfig[0]
        
        ax = c.subplots(1,1)
        ax.tick_params(
                direction='in',
                width=1,
                length=3,
                pad=2
            )
        ax.plot(testdata[0], 2*testdata[1], label='Test1')
        ax.legend()
        ax.set_title('ax title1')

        c.suptitle('fig suptitle1')

        c = subfig[1]

        axes = c.subplots(1,2)
        for ax in axes:
            ax.tick_params(
                direction='in',
                width=1,
                length=3,
                pad=2
            )
        
        ax = axes[0]

        ax.plot(testdata[1], testdata[0])
        ax.set_title('ax title2')

        ax = axes[1]

        ax.scatter(testdata[0], 0.5*testdata[1], label='Test3', color='black')
        ax.scatter(2*testdata[1], 0.5*testdata[0], label='Test4')
        ax.set_title('ax title3')

        ax.legend()

        c.suptitle('fig suptitle2')

        fig.suptitle('Suptitle')

    assert save_to1.exists() and save_to2.exists() and save_to3.exists()


if __name__ == '__main__':
    import pytest
    pytest.main()