# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024 Colin B. Macdonald

# This file tracks the various warnings that are presented to users
# when annotating, and whether they can "don't-ask-me-again".
#
# These can be relaxed/tightened on a per-server basis.  This file
# contains the static data for the initial configuration.
#
# Fields:
#     explanation: an html string that describes the situation.  This
#         can include substitutions such as ``{max_mark}``.  The
#         variables in these should be readable if the explanation
#         is viewed in a generic way.
#     allowed: if false then this situation is not allowed.  Users
#         should be shown an explanation but prevented from submitting.
#     warn: this situation is questionable.  Users can make a choice
#         after reading (hah) an explanation and making an informed
#         well-considered choice (hah!)
#     dama_allowed: users can choose to "don't ask me again".  If False,
#         users will have to answer the question every time, which can
#         get very repetitive so consider carefully before deploying the
#         case of ``warn=True`` and ``dama_allowed=False``.
#     override_allowed: instructors are able to customize this setting
#         on a per-server basis.
#
# Notes:
#   - It might be possible for some of these to be difficult/impossible
#     to realize from the client: that is ok, they are still useful
#     rules to enforce in case the client changed.  E.g., not possible
#     to get to ``zero-marks-but-has-only-ticks``?

feedback_rules = {
    "lost-marks-but-insufficient-feedback": {
        "explanation": """
            <p>You have given neither comments nor detailed annotations
            (other than &#x2713; &#x2717; &plusmn;<i>n</i>).</p>
            <p>This may make it difficult for students to learn from this
            feedback.</p>
            """,
        "allowed": True,
        "warn": True,
        "dama_allowed": True,
        "override_allowed": True,
    },
    "zero-marks-but-has-only-ticks": {
        "explanation": """
            <p>You have given 0/{max_mark}
            but there are <em>only ticks on the page!</em>
            Please confirm, or consider using comments to clarify.</p>
        """,
        "allowed": True,
        "warn": True,
        "dama_allowed": False,
        "override_allowed": False,
        # currently not realizable in modern clients
    },
    "zero-marks-but-has-ticks": {
        "explanation": """
            <p>You have given 0/{max_mark}
            but there are some ticks on the page.
            Please confirm, or consider using comments to clarify.</p>
        """,
        "allowed": True,
        "warn": True,
        "dama_allowed": True,
        "override_allowed": True,
    },
    "full-marks-but-has-only-crosses": {
        "explanation": """
            <p>You have given full {max_mark}/{max_mark}
            <em>but there are only crosses on the page!</em>
            Please confirm, or consider using comments to clarify.</p>
        """,
        "allowed": True,
        "warn": True,
        "dama_allowed": False,
        "override_allowed": False,
        # currently not realizable in modern clients
    },
    "full-marks-but-has-crosses": {
        "explanation": """
            <p>You have given full {max_mark}/{max_mark}
            but there are crosses on the page.
            Please confirm, or consider using comments to clarify.</p>
        """,
        "allowed": True,
        "warn": True,
        "dama_allowed": True,
        "override_allowed": True,
    },
    "full-marks-but-other-annotations-contradictory": {
        "explanation": """
            <p>You have given full {max_mark}/{max_mark}
            but there are other annotations on the page which might be contradictory.
            Please confirm, or consider using comments to clarify.</p>
        """,
        "allowed": True,
        "warn": True,
        "dama_allowed": True,
        "override_allowed": True,
    },
    "out-of-does-not-match-max-mark": {
        "explanation": """
            <p>This question is out of {max_mark}.
            You used {num_absolute_rubrics} absolute rubrics for a
            total &ldquo;out of&rdquo; of {out_of}.</p>
            <p>Are you sure you finished marking this question?</p>
        """,
        "allowed": True,
        "warn": True,
        "dama_allowed": True,
        "override_allowed": True,
    },
    "confusing-to-mix-abs-minus-relative": {
        "explanation": """
            <p>Its probably confusing to combine absolute rubrics such as</p>
            <blockquote>
              {exemplar}
            </blockquote>
            <p>with negative relative rubrics such as</p>
            <blockquote>
              {exemplar2}
            </blockquote>
            <p>because the reader may be uncertain what is changed by that
              &ldquo;{exemplar2_display_delta}&rdquo;.
            </p>
            <p>Are you sure this feedback will be understandable?</p>
        """,
        "allowed": True,
        "warn": True,
        "dama_allowed": True,
        "override_allowed": True,
    },
    "confusing-to-mix-abs-plus-relative": {
        "explanation": """
            <p>Combining absolute rubrics such as</p>
            <blockquote>
              {exemplar1}
            </blockquote>
            <p>with positive relative rubrics such as</p>
            <blockquote>
              {exemplar2}
            </blockquote>
            <p>is potentially confusing.</p>
            <p>You may want to <em>check with your team</em>
            to decide if this case is acceptable or not.</p>
            <p>Do you want to continue?</p>
        """,
        "allowed": True,
        "warn": True,
        "dama_allowed": True,
        "override_allowed": True,
    },
    "each-page-should-be-annotated": {
        "explanation": """
            <p>A page without annotation may leave students wondering
            if you saw their work on this page.</p>
            <p>Page(s) {which_pages} of those shown have no annotations.</p>
            <p>Consider leaving some sort of feedback on each
            part of a student's work: for example, a highlighted
            rectangle around a paragraph acknowledges that you saw it,
            without committing you to commenting on its correctness.</p>
            <p>If a page is blank then we suggest drawing a diagonal
            red line across the page.</p>
        """,
        "allowed": True,
        "warn": True,
        "dama_allowed": True,
        "override_allowed": True,
    },
    # These not implemented yet: Issue #2037
    "mix-up-and-down-rubrics-unambiguous-case": {
        "explanation": """
            Mixing up and down.
            TODO: not implemented.  Well, its forbidden just not connected to this system.
        """,
        "allowed": False,
        "warn": True,
        "dama_allowed": False,
        "override_allowed": False,
    },
    "mix-up-and-down-rubrics-ambiguous-case": {
        "explanation": "TODO: not implemented within this system",
        "allowed": False,
        "warn": True,
        "dama_allowed": False,
        "override_allowed": False,
    },
}
