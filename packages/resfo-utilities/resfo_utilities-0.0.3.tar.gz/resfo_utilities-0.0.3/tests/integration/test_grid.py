import pytest
from pathlib import Path
from textwrap import dedent, indent
import subprocess
from resfo_utilities import CornerpointGrid, MapAxes
from pytest import approx
from dataclasses import dataclass


@dataclass
class AdditionalDeckContents:
    runspec: str = ""
    grid: str = ""


@pytest.fixture(
    params=[
        pytest.param(AdditionalDeckContents(), id="Only global grid"),
        pytest.param(
            AdditionalDeckContents(
                runspec=dedent("""\
                LGR
                1 8 3*0
                /
                 """),
                grid=dedent("""\
                CARFIN
                'LGR1' 6*2 4*2
                /
                ENDFIN
                 """),
            ),
            id="With one LGR grid",
        ),
    ]
)
def eightcells(request, simulator_cmd: list[str], tmp_path: Path) -> None:
    additions = request.param
    if simulator_cmd[0].endswith("flow") and "LGR" in additions.runspec:
        pytest.skip(reason="flow does not support LGR")
    nl = "\n"
    (tmp_path / "EIGHTCELLS.DATA").write_text(
        dedent(
            f"""\
        RUNSPEC

        DIMENS
        2 2 2 /

        OIL
        WATER

        START
        1 'JAN' 2000 /

        TABDIMS
        1 1 20 20 2 /

        EQLDIMS
        1 /

        WELLDIMS
        1 1 1 1 /

        WSEGDIMS
        1 10 10 /

        UNIFOUT

        {nl + indent(additions.runspec, " " * 8)}

        GRID

        NEWTRAN

        COORD
            0.1   0.2   0.3     0.4   0.5 100.6
           50.7   0.8   0.9    51.1   1.2 101.3
          101.4   1.5   1.6   101.7   1.8 101.9
            2.0  52.1   2.3     2.4  52.5 102.6
           52.7  52.8   2.9    53.0  53.1 103.2
          103.3  53.4   3.5   103.6  53.7 103.8
            3.9 104.0   4.1     4.2 104.3 104.4
           54.5 104.6   4.7    54.8 104.9 105.0
          105.1 105.2   5.3   105.4 105.5 105.6
        /

        ZCORN
        0.0 0.1 0.2 0.3
        0.4 0.5 0.6 0.7
        0.8 0.9 1.0 1.1
        1.2 1.3 1.4 1.5
        50.0 50.1 50.2 50.3
        50.4 50.5 50.6 50.7
        50.8 50.9 51.0 51.1
        51.2 51.3 51.4 51.5
        51.6 51.7 51.8 51.9
        52.0 52.1 52.2 52.3
        52.4 52.5 52.6 52.7
        52.8 52.9 53.0 53.1
        100.0 100.1 100.2 100.3
        100.4 100.5 100.6 100.7
        100.8 100.9 101.0 101.1
        101.2 101.3 101.4 101.5
        /

        -- X1 Y1 X2 Y2 X3 Y3
        MAPAXES
         0.01 1.01 0.01 0.01 1.01 0.01 /


        PORO
        0.2  0.2  0.2  0.2   0.2  0.2  0.2  0.2
        /

        PERMX
        100.0  100.0  100.0  100.0    100.0  100.0  100.0  100.0
        /

        PERMY
        100.0  100.0  100.0  100.0    100.0  100.0  100.0  100.0
        /

        PERMZ
        100.0  100.0  100.0  100.0    100.0  100.0  100.0  100.0
        /


        GRIDFILE
        0 1
        /

        {nl + indent(additions.grid, " " * 8)}

        INIT

        PROPS


        SWOF
        -- SW KRW KROW PC
        0.1 0 1 1
        1 1.0 0.0 0
        /


        DENSITY
        800 1000 1.2 /

        PVTW
        1 1 0.0001 0.2 0.00001 /

        PVDO
        10 1   1
        150 0.9 1 /

        ROCK
        100 0.0001 /

        FILLEPS

        REGIONS

        SATNUM
        1  1  1  1  1  1  1  1/

        EQLNUM
        1  1  1  1  1  1  1  1/

        FIPNUM
        1 1 1 1 2 2 2 2
        /

        SOLUTION

        EQUIL
        -- datum pressure_datum owc/gwc pc@owc goc pc@goc item7 item8 oip_init
        100 100 50 /


        RPTRST
        ALLPROPS/

        SUMMARY
        FOPR
        FOPT
        WOPT
        /
        WOPR
        /
        CPI
        OP1 /
        /

        SCHEDULE

        WELSPECS
        OP1 OPS 1 1 50 OIL /
        /

        COMPDAT
        OP1 1 1 1 1 OPEN 1* 1* 0.15  /
        /


        WELSEGS
        OP1 5 5 1* INC /
        2 2 1 1 10 10  0.015 0.0001 /
        /

        COMPSEGS
        OP1 /
        --i j k branch len
        1 1 1 1      10 20 Z /
        /

        WRFTPLT
        '*' YES YES YES  /
        /

        WCONPROD
        OP1 OPEN ORAT 50 /
        /

        TSTEP
        1 1 /
        """
        )
    )


@pytest.mark.usefixtures("eightcells")
def test_that_we_can_read_the_eightcells_grid_from_the_simulator(
    tmp_path: Path, simulator_cmd: list[str]
) -> None:
    subprocess.run(simulator_cmd + [str(tmp_path / "EIGHTCELLS")])

    grid = CornerpointGrid.read_egrid(str(tmp_path / "EIGHTCELLS.EGRID"))

    assert grid.coord.shape == (3, 3, 2, 3)
    assert grid.coord[0, 0].tolist() == [
        approx([0.1, 0.2, 0.3]),
        approx([0.4, 0.5, 100.6]),
    ]
    assert grid.coord[1, 0].tolist() == [
        approx([50.7, 0.8, 0.9]),
        approx([51.1, 1.2, 101.3]),
    ]
    assert grid.coord[2, 0].tolist() == [
        approx([101.4, 1.5, 1.6]),
        approx([101.7, 1.8, 101.9]),
    ]
    assert grid.coord[0, 1].tolist() == [
        approx([2.0, 52.1, 2.3]),
        approx([2.4, 52.5, 102.6]),
    ]
    assert grid.coord[1, 1].tolist() == [
        approx([52.7, 52.8, 2.9]),
        approx([53.0, 53.1, 103.2]),
    ]
    assert grid.coord[2, 1].tolist() == [
        approx([103.3, 53.4, 3.5]),
        approx([103.6, 53.7, 103.8]),
    ]
    assert grid.coord[0, 2].tolist() == [
        approx([3.9, 104.0, 4.1]),
        approx([4.2, 104.3, 104.4]),
    ]
    assert grid.coord[1, 2].tolist() == [
        approx([54.5, 104.6, 4.7]),
        approx([54.8, 104.9, 105.0]),
    ]
    assert grid.coord[2, 2].tolist() == [
        approx([105.1, 105.2, 5.3]),
        approx([105.4, 105.5, 105.6]),
    ]

    assert grid.zcorn.shape == (2, 2, 2, 8)
    # Order of heights for each corner is
    # (N(orth) means higher y, E(east) means higer x, T(op) means lower z (depth))
    # TSW TSE TNW TNE BSW BSE BNW BNE
    assert grid.zcorn[0, 0, 0, :].tolist() == approx(
        [0.0, 0.1, 0.4, 0.5, 50.0, 50.1, 50.4, 50.5],
    )
    assert grid.zcorn[1, 0, 0, :].tolist() == approx(
        [0.2, 0.3, 0.6, 0.7, 50.2, 50.3, 50.6, 50.7],
    )
    assert grid.zcorn[0, 1, 0, :].tolist() == approx(
        [0.8, 0.9, 1.2, 1.3, 50.8, 50.9, 51.2, 51.3],
    )
    assert grid.zcorn[1, 1, 0, :].tolist() == approx(
        [1.0, 1.1, 1.4, 1.5, 51.0, 51.1, 51.4, 51.5],
    )
    assert grid.zcorn[0, 0, 1, :].tolist() == approx(
        [51.6, 51.7, 52.0, 52.1, 100.0, 100.1, 100.4, 100.5],
    )
    assert grid.zcorn[1, 0, 1, :].tolist() == approx(
        [51.8, 51.9, 52.2, 52.3, 100.2, 100.3, 100.6, 100.7],
    )
    assert grid.zcorn[0, 1, 1, :].tolist() == approx(
        [52.4, 52.5, 52.8, 52.9, 100.8, 100.9, 101.2, 101.3],
    )
    assert grid.zcorn[1, 1, 1, :].tolist() == approx(
        [52.6, 52.7, 53.0, 53.1, 101.0, 101.1, 101.4, 101.5],
    )
    assert grid.map_axes == MapAxes(
        y_axis=approx((0.01, 1.01)),
        origin=approx((0.01, 0.01)),
        x_axis=approx((1.01, 0.01)),
    )

    assert grid.point_in_cell((25, 25, 25), 0, 0, 0)
    assert grid.find_cell_containing_point([(25, 25, 25)]) == [(0, 0, 0)]
    assert grid.find_cell_containing_point([(200, 200, 200)]) == [None]
    assert not grid.point_in_cell((225, 225, 225), 0, 0, 0)
