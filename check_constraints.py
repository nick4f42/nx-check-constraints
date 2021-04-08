"""Displays each ill-constrained sketch in the active part."""

import time

import NXOpen
import NXOpen.UF


def main():
    session  = NXOpen.Session.GetSession()
    uf_session = NXOpen.UF.UFSession.GetUFSession()

    lw = session.ListingWindow
    lw.Open()

    work_part = session.Parts.Work

    # Find all bad constraints
    bad_constraints = []
    for sketch in work_part.Sketches:
        # Returns (number of sketch dimensions, list of dimension tags)
        dims, tags = uf_session.Sket.AskDimensionsOfSketch(sketch.Tag)

        # Count the number of each type of dimension
        num_driving = 0
        num_ref = 0
        num_auto = 0
        for tag in tags:
            dim_status = uf_session.Sket.AskDimStatus(tag)
            exp_tag = dim_status[0]
            ref_status = uf_session.Sket.AskReferenceStatus(sketch.Tag, tag)

            if ref_status is NXOpen.UF.Sket.ReferenceStatus.REFERENCE:
                num_ref += 1
            elif not exp_tag:
                num_auto += 1
            else:
                num_driving += 1
        
        # Returns (status enum, degrees of freedom needed)
        status, dof_needed = sketch.GetStatus()

        if status is not sketch.Status.WellConstrained or num_auto != 0:
            bad_constraints.append({
                'sketch': sketch,
                'feature': work_part.Features.GetAssociatedFeature(sketch),
                'status': status,
                'dof_needed': dof_needed,
                'num_driving': num_driving,
                'num_auto': num_auto,
            })

    # Focus view on each bad constraint
    for i, bad in enumerate(bad_constraints):
        bad['sketch'].Activate(NXOpen.SketchViewReorient.TrueValue)
        if i != len(bad_constraints) - 1:
            time.sleep(2)
        bad['sketch'].Deactivate(NXOpen.SketchViewReorient.FalseValue,
                                 NXOpen.SketchUpdateLevel.SketchOnly)

    # Log each ill-constrained sketch to listing window
    if bad_constraints:
        # Highlight the last sketch
        bad['sketch'].Highlight()

        if len(bad_constraints) == 1:
            msg0 = "sketch is"
        else:
            msg0 = "sketches are"
        msg = f"Oops! {len(bad_constraints)} {msg0} improperly constrained."
        msg = msg.center(56)

        lw.WriteLine(msg)
        lw.WriteLine("=" * len(msg))
        for i in bad_constraints:
            print_constraint(lw, i)
            lw.WriteLine("-" * len(msg))
    else:
        lw.WriteLine("Part is fully constrained :)")


def print_constraint(lw, d):
    """Print the constraint described by dict d to ListingWindow lw.

    Args:
        lw: The ListingWindow to print to.
        d: dict that holds information about the ill-constrained sketch.
    """
    # If feature has a custom name, include it
    name = d['feature'].GetFeatureName()
    if d['feature'].Name:
        name += ':' + d['feature'].Name
    lw.WriteLine(name)
        
    if d['dof_needed'] != 0:
        lw.WriteLine("\tSketch needs {} more constraint(s).".format(d['dof_needed']))

    if d['status'] is NXOpen.SketchStatus.OverConstrained:
        lw.WriteLine("\tSketch is over-constrained.")
    elif d['status'] is NXOpen.SketchStatus.Unknown:
        lw.WriteLine("\tSketch has unknown status.")
    elif d['status'] is NXOpen.SketchStatus.NotEvaluated:
        lw.WriteLine("\tSketch status not evaluated.")
    elif d['status'] is NXOpen.SketchStatus.InconsistentlyConstrained:
        lw.WriteLine("\tSketch has conflicting constraints.")

    if d['num_auto'] != 0:
        lw.WriteLine("\tSketch has {} auto dimension(s) remaining.".format(d['num_auto']))


if __name__ == '__main__':
    main()
