# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2024 Andrew Rechnitzer
# Copyright (C) 2020-2025 Colin B. Macdonald
# Copyright (C) 2020 Victoria Schuster
# Copyright (C) 2024 Bryan Tanady

"""Elastic band options for connecting rubrics to labels."""

import logging

from PyQt6.QtCore import QLineF, QPointF, QRectF
from PyQt6.QtGui import QPainterPath


log = logging.getLogger("scene")


# things for nice rubric/text drag-box tool
# work out how to draw line from current point
# to nearby point on a given rectangle
# also need a minimum size threshold for that box
# in order to avoid drawing very very small boxes
# by accident when just "clicking"
# see #1435

minimum_box_side_length = 24


def shape_to_sample_points_on_boundary(shape, corners=False, all_sides=True):
    """Return some points on the perimeter of a shape.

    If the input is a point, just return that point.

    If the input is a rectangle, by default, list of vertices in the
    middle of each side, but this can be adjusted.
    """
    if isinstance(shape, QRectF):
        x, y, w, h = shape.getRect()
        # start with midpoints of the rectangle sides
        if all_sides:
            pts = [
                QPointF(x + w / 2, y),
                QPointF(x + w / 2, y + h),
                QPointF(x, y + h / 2),
                QPointF(x + w, y + h / 2),
            ]
        else:
            pts = [
                QPointF(x, y + h / 2),
                QPointF(x + w, y + h / 2),
            ]
        if corners:
            pts += [
                QPointF(x, y),
                QPointF(x + w, y),
                QPointF(x, y + h),
                QPointF(x + w, y + h),
            ]
        return pts
    elif isinstance(shape, QPointF):
        return [shape]
    else:
        raise ValueError(f"Don't know how find points on perimeter of {shape}")


def sqrDistance(vect):
    """Return the l2 norm of a 2d-vector."""
    return vect.x() * vect.x() + vect.y() * vect.y()


def shortestLine(g_rect, b_rect):
    """Get approximately shortest line between two shapes.

    More precisely, given two rectangles, return shortest line between the midpoints of their sides. A single-vertex is treated as a rectangle of height/width=0 for this purpose.
    """
    gvert = shape_to_sample_points_on_boundary(g_rect, corners=False)
    bvert = shape_to_sample_points_on_boundary(
        b_rect,
        corners=True,
    )
    gp = gvert[0]
    bp = bvert[0]
    dd = sqrDistance(gp - bp)
    for p in gvert:
        for q in bvert:
            dst = sqrDistance(p - q)
            if dst < dd:
                gp = p
                bp = q
                dd = dst
    return QLineF(bp, gp)


def which_classic_shortest_corner_side(ghost, r):
    """Get approximately shortest line between corners/midpoints of two rectangles.

    Args:
        ghost (QRect/QPointF): considers the midpoints only.
        r (QRect): uses the midpoints and corners.

    Returns:
        QPainterPath
    """
    line = shortestLine(ghost, r)
    path = QPainterPath(line.p1())
    path.lineTo(line.p2())
    return path


def _get_intersection_bw_rect_line(rec, lin):
    """Return the intersection between a line and rectangle or None."""
    if isinstance(rec, QPointF):
        return None
    x, y, w, h = rec.getRect()
    yes, pt = lin.intersects(QLineF(QPointF(x, y), QPointF(x + w, y)))
    if yes == QLineF.IntersectionType.BoundedIntersection:
        return pt
    yes, pt = lin.intersects(QLineF(QPointF(x + w, y), QPointF(x + w, y + h)))
    if yes == QLineF.IntersectionType.BoundedIntersection:
        return pt
    yes, pt = lin.intersects(QLineF(QPointF(x + w, y + h), QPointF(x, y + h)))
    if yes == QLineF.IntersectionType.BoundedIntersection:
        return pt
    yes, pt = lin.intersects(QLineF(QPointF(x, y + h), QPointF(x, y)))
    if yes == QLineF.IntersectionType.BoundedIntersection:
        return pt
    return None


def which_centre_to_centre(ghost, r):
    """Get approximately shortest line between two shapes "center-to-centre".

    Args:
        ghost (QRect/QPointF): a shape.
        r (QRect): another shape.

    Returns:
        QPainterPath
    """
    if isinstance(ghost, QPointF):
        A = ghost
    else:
        x, y, w, h = ghost.getRect()
        A = QPointF(x + w / 2, y + h / 2)
    if isinstance(r, QPointF):
        B = r
    else:
        x, y, w, h = r.getRect()
        B = QPointF(x + w / 2, y + h / 2)
    CtoC = QLineF(A, B)
    A = _get_intersection_bw_rect_line(ghost, CtoC)
    B = _get_intersection_bw_rect_line(r, CtoC)
    if A is None or B is None:
        # probably inside
        return which_classic_shortest_corner_side(ghost, r)
    path = QPainterPath(A)
    path.lineTo(B)
    return path


def which_sticky_corners(g, r):
    """Choose an aesthetically-pleasing (?) line between the rectangle and the ghost.

    Args:
        g (QRect/QPointF): The ghost, can be rect or a point.
        r (QRect): a rectangle.

    Returns:
        QPainterPath
    """
    if isinstance(g, QPointF):
        g = QRectF(g, g)

    # slope parameter > 1, determines the angle before we unsnap from corners
    slurp = 3

    def transf(t):
        """Transform function for the box.

        Each side is mapped to t in [0, 1] which is used for a linear
        interpolation, but we can pass t through a transform.  Some overlap
        between this and the slurp parameter.

        Here we implement a p.w. linear regularized double-step.
        """
        p = 0.15
        assert p < 0.25
        if t <= p:
            return 0.0
        if t <= 0.5 - p:
            return (0.5 / (0.5 - p - p)) * (t - p)
        if t <= 0.5 + p:
            return 0.5
        if t <= 1 - p:
            return (0.5 / (0.5 - p - p)) * (t - (0.5 + p)) + 0.5
        else:
            return 1.0

    def capped_ramp(crit1, crit2, x):
        """Map x into [crit1, crit2] returning a scalar in [0, 1]."""
        t = (x - crit1) / (crit2 - crit1)
        t = min(t, 1)
        t = max(0, t)
        # comment out for non-sticky midpoints
        t = transf(t)
        return t

    def ramble(a, b, left, right):
        """Some kind of soft thresholding of an interval near two points a and b.

        Consider sliding the little figure ``l-m-r`` through two values a and b.
        We want to return a value ``{r, a, m, b, l}`` depending where ``l-m-r``
        lies compared to ``[a, b]``.  Roughly, if m is in ``[A, B]`` then we
        return m, otherwise, some soft thresholding near a and b.

        The capital letters in the follow diagram illustrate the return value::

                              a                   b
                              |     return M      |
                     ⎧  l-m-R |                   | L-m-r  ⎫
              return ⎪   l-m-R|                   |L-m-r   ⎪ return
              R or A ⎨    l-m-A                   B-m-r    ⎬ B or L
                     ⎪     l-mAr                 lBm r     ⎪
                     ⎩      l-A-r               l-Br       ⎭
                             l|M-r             l-M|r
                              l-M-r           l-M-r
                              |l-M-r  l-M-r  l-M-r|
                              |                   |
        """
        mid = (left + right) / 2
        if right <= a:
            return right
        elif mid <= a:
            return a
        elif left >= b:
            return left
        elif mid >= b:
            return b
        return mid

    # We cut up the space around "r" into four regions by the eikonal solution
    # shocks.  Then we process each of those 4 regions.  For example the "top"
    # region looks like this, showing also two ghosts that should be considered
    # "in" this region.
    #                  /
    # \            +----+
    # +---+       g| /  |
    # | \ |g       +----+
    # +---+        /
    #     \       /
    #      +-----+
    #      |  r  |
    #      +-----+
    if (
        g.bottom() <= r.top()
        and g.bottom() <= r.top() - (g.left() - r.right())
        and g.bottom() <= r.top() - (r.left() - g.right())
    ):
        crit1 = r.left() - (r.top() - g.bottom()) / slurp
        crit2 = r.right() + (r.top() - g.bottom()) / slurp
        t = capped_ramp(crit1, crit2, (g.left() + g.right()) / 2)
        gx = ramble(crit1, crit2, g.left(), g.right())
        # return QLineF(r.left() + t * r.width(), r.top(), gx, g.bottom())
        path = QPainterPath(QPointF(r.left() + t * r.width(), r.top()))
        path.lineTo(QPointF(gx, g.bottom()))
        return path

    if (
        g.top() >= r.bottom()
        and g.top() >= r.bottom() + g.left() - r.right()
        and g.top() >= r.bottom() + r.left() - g.right()
    ):
        crit1 = r.left() - (g.top() - r.bottom()) / slurp
        crit2 = r.right() + (g.top() - r.bottom()) / slurp
        t = capped_ramp(crit1, crit2, (g.left() + g.right()) / 2)
        gx = ramble(crit1, crit2, g.left(), g.right())
        # return QLineF(r.left() + t * r.width(), r.bottom(), gx, g.top())
        path = QPainterPath(QPointF(r.left() + t * r.width(), r.bottom()))
        path.lineTo(QPointF(gx, g.top()))
        return path

    if g.left() >= r.right():
        crit1 = r.top() - (g.left() - r.right()) / slurp
        crit2 = r.bottom() + (g.left() - r.right()) / slurp
        t = capped_ramp(crit1, crit2, (g.top() + g.bottom()) / 2)
        gy = ramble(crit1, crit2, g.top(), g.bottom())
        # return QLineF(r.right(), r.top() + t * r.height(), g.left(), gy)
        path = QPainterPath(QPointF(r.right(), r.top() + t * r.height()))
        path.lineTo(QPointF(g.left(), gy))
        return path

    if g.right() <= r.left():
        crit1 = r.top() - (r.left() - g.right()) / slurp
        crit2 = r.bottom() + (r.left() - g.right()) / slurp
        t = capped_ramp(crit1, crit2, (g.top() + g.bottom()) / 2)
        gy = ramble(crit1, crit2, g.top(), g.bottom())
        # return QLineF(r.left(), r.top() + t * r.height(), g.right(), gy)
        path = QPainterPath(QPointF(r.left(), r.top() + t * r.height()))
        path.lineTo(QPointF(g.right(), gy))
        return path

    # return which_classic_shortest_corner_side(g, r)
    # TODO: Issue #1892, for now, just a degenerate path
    path = QPainterPath(QPointF(r.left(), r.top()))
    # ... or extend to a degenerate line?
    # path.lineTo(QPointF(r.left(), r.top()))
    return path


def get_midpoints(shape):
    """Get a dict of the midpoints of each side of the given shape."""
    if isinstance(shape, QRectF):
        x, y, w, h = shape.getRect()
        return {
            "west": QPointF(x, y + h / 2),
            "east": QPointF(x + w, y + h / 2),
            "north": QPointF(x + w / 2, y),
            "south": QPointF(x + w / 2, y + h),
        }
    elif isinstance(shape, QPointF):
        return {
            "west": shape,
            "east": shape,
            "north": shape,
            "south": shape,
        }
    else:
        raise ValueError(f"Don't know how find points on perimeter of {shape}")


def short_lines(
    b_pts,
    a_pt,
    *,
    N=2,
    check_only_north=False,
    check_only_west=False,
    check_only_east=False,
):
    """Get lines from b_pts to a_pt sorted shortest to longest.

    KWargs:
        N: how many short lines to return.
        check_only_north: when True, only check b_pts that lie
            to the north of a_pt.
        check_only_west: when True, only check b_pts that lie
            to the west of a_pt.
        check_only_east: when True, only check b_pts that lie
            to the east of a_pt.

    Returns: List of the shortest N lines from points in b_pts to a_pt.
    """
    if check_only_north:
        b_pts = [b for b in b_pts if b.y() <= a_pt.y()]
    if check_only_west:
        b_pts = [b for b in b_pts if b.x() <= a_pt.x()]
    if check_only_east:
        b_pts = [b for b in b_pts if b.x() >= a_pt.x()]

    distances_and_lines = sorted(
        [(sqrDistance(a_pt - b), QLineF(b, a_pt)) for b in b_pts],
        key=lambda X: X[0],
    )
    return [X[1] for X in distances_and_lines[:N]]


def shortestToSideLine(g_rect, b_rect):
    """Find a 'nice' line connecting the ghost-rect to the box.

    Returns the line and a bool. The bool indicates whether or not the
    line connects to the east or west side of the ghost-rect.
    """
    # based heavily on work/ideas by BryanT in !2720.
    # though I suggest we merge this instead of that

    # get the midpoints of the ghost-rect boundary,
    g_midpoints = get_midpoints(g_rect)
    # and the midpoints and corners of the box-boundary
    bvert = shape_to_sample_points_on_boundary(b_rect, corners=True)
    # determine if center of ghost is north of the box
    ghost_is_south = g_rect.center().y() >= b_rect.top()
    # we first try to connect the west side of the g_rect to the box.
    # however, if the centre of the ghost is south of the top-edge of the box,
    # then we try to connect west/north
    # first try to connect left-mid-side of g_rect to box, and make sure
    # the connecting line goes to the west.
    lines_to_west = short_lines(
        bvert,
        g_midpoints["west"],
        check_only_north=ghost_is_south,
        check_only_west=True,
    )
    for line in lines_to_west:
        return line, True

    # if no suitable line try to connect to the east with similar reasoning.
    lines_to_east = short_lines(
        bvert,
        g_midpoints["east"],
        check_only_north=ghost_is_south,
        check_only_east=True,
    )
    for line in lines_to_east:
        return line, True
    # if that doesn't work try to connect to middle of north side
    line_to_north = short_lines(bvert, g_midpoints["north"], N=1)[0]
    # but only if line runs in correct direction
    if line_to_north.p1().y() <= line_to_north.p2().y():
        return line_to_north, False
    # all else fails - connect to the middle of south side
    line_to_south = short_lines(bvert, g_midpoints["south"], N=1)[0]
    return line_to_south, False


def which_horizontal_step(g_rect, b_rect):
    """WIP on a beautiful horizontally stepped labelling system.

    Args:
        g_rect (QRect/QPointF): The ghost, can be rect or a point.
        b_rect (QRect): the box on the page.

    Returns:
        QPainterPath
    """
    # direct line from the box-rect to the ghost-rect
    directLine, connects_east_west = shortestToSideLine(g_rect, b_rect)
    thePath = QPainterPath(directLine.p1())

    # iteration 1
    # draw a path as vertical and then horizontal components.
    # thePath.lineTo(directLine.x1(), directLine.y2())
    # thePath.lineTo(directLine.p2())

    # iteration 2
    # draw path as diagonal followed by flat
    # sg = directLine.dy() * directLine.dx()  # get sign of gradient
    # if abs(directLine.dy()) < abs(directLine.dx()):  # end in horizontal
    #     sx = directLine.dy()
    #     if sg < 0:  # flip sign if gradient negative
    #         sx = -sx
    #     thePath.lineTo(directLine.x1() + sx, directLine.y2())
    #     thePath.lineTo(directLine.p2())
    # else:  # end in vertical
    #     sy = directLine.dx()
    #     if sg < 0:  # flip sign if gradient negative
    #         sy = -sy
    #     thePath.lineTo(directLine.x2(), directLine.y1() + sy)
    #     thePath.lineTo(directLine.p2())

    # iteration 3
    # as #2 but steeper diagonal
    slope = 3
    sg = directLine.dy() * directLine.dx()  # get sign of gradient
    if connects_east_west and (
        abs(directLine.dy()) < slope * abs(directLine.dx())
    ):  # end in horizontal
        sx = directLine.dy() / slope
        if sg < 0:  # flip sign if gradient negative
            sx = -sx
        thePath.lineTo(directLine.x1() + sx, directLine.y2())
        thePath.lineTo(directLine.p2())
    else:  # too steep - so draw single connecting line segment
        thePath.lineTo(directLine.p2())

    return thePath
