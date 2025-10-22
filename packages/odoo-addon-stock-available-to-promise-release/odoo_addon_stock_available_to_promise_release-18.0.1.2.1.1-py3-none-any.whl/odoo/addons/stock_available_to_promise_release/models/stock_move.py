# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# Copyright 2020 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# Copyright 2025 Raumschmiede GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import itertools
import logging
import operator as py_operator
from collections import defaultdict

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import date_utils, float_compare, float_is_zero, float_round, groupby

from odoo.addons.stock.models.stock_move import StockMove as StockMoveBase

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    date_priority = fields.Datetime(
        string="Priority Date",
        index=True,
        default=fields.Datetime.now,
        help="Date/time used to sort moves to deliver first. "
        "Used to calculate the ordered available to promise.",
    )
    previous_promised_qty = fields.Float(
        string="Quantity Promised before this move",
        compute="_compute_previous_promised_qty",
        digits="Product Unit of Measure",
        help="Quantities promised to moves with higher priority than this move "
        "(in default UoM of the product).",
    )
    ordered_available_to_promise_qty = fields.Float(
        string="Ordered Available to Promise (Real Qty)",
        compute="_compute_ordered_available_to_promise",
        digits="Product Unit of Measure",
        help="Available to Promise quantity minus quantities promised "
        " to moves with higher priority (in default UoM of the product).",
    )
    ordered_available_to_promise_uom_qty = fields.Float(
        string="Ordered Available to Promise",
        compute="_compute_ordered_available_to_promise",
        search="_search_ordered_available_to_promise_uom_qty",
        digits="Product Unit of Measure",
        help="Available to Promise quantity minus quantities promised "
        " to moves with higher priority (in initial demand's UoM).",
    )
    release_ready = fields.Boolean(
        compute="_compute_release_ready",
        search="_search_release_ready",
    )
    need_release = fields.Boolean(index=True, copy=False)
    unrelease_allowed = fields.Boolean(compute="_compute_unrelease_allowed")

    @api.depends("need_release", "rule_id", "rule_id.available_to_promise_defer_pull")
    def _compute_unrelease_allowed(self):
        user_is_allowed = self.env.user.has_group("stock.group_stock_user")
        for move in self:
            unrelease_allowed = user_is_allowed and move._is_unreleaseable()
            if unrelease_allowed:
                iterator = move._get_chained_moves_iterator("move_orig_ids")
                next(iterator)  # skip the current move
                for origin_moves in iterator:
                    unrelease_allowed = (
                        not origin_moves._in_progress_for_unrelease()
                        and move._is_unrelease_allowed_on_origin_moves(origin_moves)
                    )
                    if not unrelease_allowed:
                        break
            move.unrelease_allowed = unrelease_allowed

    def _is_unreleaseable(self):
        """Check if the move can be unrelease. At this stage we only check if
        the move is at the end of a chain of moves and has the caracteristics
        to be unrelease. We don't check the conditions on the origin moves.
        The conditions on the origin moves are checked in the method
        _is_unrelease_allowed_on_origin_moves.
        """
        self.ensure_one()
        return (
            not self.need_release
            and self.state not in ("done", "cancel")
            and self.picking_type_id.code == "outgoing"
            and self.rule_id.available_to_promise_defer_pull
        )

    def _has_unreleasable_state(self):
        self.ensure_one()
        if self.rule_id.allow_unrelease_return_done_move:
            blocking_states = ("cancel",)
        else:
            blocking_states = ("done", "cancel")
        return self.state not in blocking_states

    def _in_progress_for_unrelease(self) -> StockMoveBase:
        """
        This method will return the moves with unreleasable state that :

        - have their picking printed
        - have a quantity done set if allow_unrelease_return_done_move
        """
        unreleasable_moves = self.filtered(lambda m: m._has_unreleasable_state())
        if not unreleasable_moves:
            return unreleasable_moves
        printed_pickings = unreleasable_moves.filtered("picking_id.printed")
        if printed_pickings:
            return printed_pickings
        return unreleasable_moves.filtered(
            lambda m: not m.rule_id.allow_unrelease_return_done_move
            and any(ml.quantity > 0 and ml.picked for ml in m.move_line_ids)
        )

    def _is_unrelease_allowed_on_origin_moves(self, origin_moves):
        """We check that the origin moves are in a state that allows the unrelease
        of the current move. At this stage, a move can't be unreleased if
        the processed origin moves is not consumed by the dest moves.
        """
        self.ensure_one()
        origin_done_moves = origin_moves.filtered(lambda m: m.state == "done")
        if self.rule_id.allow_unrelease_return_done_move:
            origin_done_moves = origin_done_moves.filtered(
                lambda m: not m.picking_type_id.return_picking_type_id
            )
        origin_qty_done = sum(
            m.product_uom._compute_quantity(
                m.quantity,
                m.product_id.uom_id,
                rounding_method="HALF-UP",
            )
            for m in origin_done_moves
        )
        dest_done_moves = origin_done_moves.move_dest_ids
        dest_qty_done = sum(
            m.product_uom._compute_quantity(
                sum(ml.quantity for ml in m.move_line_ids if ml.picked),
                m.product_id.uom_id,
                rounding_method="HALF-UP",
            )
            for m in dest_done_moves
        )
        return (
            float_compare(
                origin_qty_done,
                dest_qty_done,
                precision_rounding=self.product_id.uom_id.rounding,
            )
            <= 0
        )

    def _unrelease_not_allowed_error(self):
        message = self.env._("You are not allowed to unrelease those deliveries:\n")

        for picking, forbidden_moves_by_picking in groupby(
            self, lambda m: m.picking_id
        ):
            forbidden_moves_by_picking = self.browse().concat(
                *forbidden_moves_by_picking
            )
            message += f"\n\t- {picking.name}"
            forbidden_origin_pickings = self.picking_id.browse()
            for move in forbidden_moves_by_picking:
                iterator = move._get_chained_moves_iterator("move_orig_ids")
                next(iterator)  # skip the current move
                for origin_moves in iterator:
                    for origin_picking, moves_by_picking in groupby(
                        origin_moves, lambda m: m.picking_id
                    ):
                        moves_by_picking = self.browse().concat(*moves_by_picking)
                        if not move._is_unrelease_allowed_on_origin_moves(
                            moves_by_picking
                        ):
                            forbidden_origin_pickings |= origin_picking
            if forbidden_origin_pickings:
                message += " "
                message += self.env._(
                    "- blocking transfer(s): %(picking_names)s",
                    picking_names=" ".join(forbidden_origin_pickings.mapped("name")),
                )
        raise UserError(message)

    def _previous_promised_qty_sql_main_query(self):
        return """
            SELECT move.id,
                   COALESCE(SUM(previous_moves.previous_qty), 0.0)
            FROM stock_move move
            LEFT JOIN LATERAL (
                SELECT
                    m.product_qty
                    AS previous_qty
                FROM stock_move m
                INNER JOIN stock_location loc
                ON loc.id = m.location_id
                LEFT JOIN stock_picking_type p_type
                ON m.picking_type_id = p_type.id
                WHERE
                {lateral_where}
                GROUP BY m.id
            ) previous_moves ON true
            WHERE
            move.id IN %(move_ids)s
            GROUP BY move.id;
        """

    def _previous_promised_qty_sql_moves_before_matches(self):
        return "COALESCE(m.need_release, False) = COALESCE(move.need_release, False)"

    def _previous_promised_qty_sql_moves_before(self):
        sql = f"""
            {self._previous_promised_qty_sql_moves_before_matches()}
            AND (
                m.priority > move.priority
                OR
                (
                    m.priority = move.priority
                    AND m.date_priority < move.date_priority
                )
                OR (
                    m.priority = move.priority
                    AND m.date_priority = move.date_priority
                    AND m.picking_type_id = move.picking_type_id
                    AND m.id < move.id
                )
                OR (
                    m.priority = move.priority
                    AND m.date_priority = move.date_priority
                    AND m.picking_type_id != move.picking_type_id
                    AND m.id > move.id
                )
            )
        """
        return sql

    def _previous_promised_qty_sql_moves_no_release(self):
        return "m.need_release IS false OR m.need_release IS null"

    def _previous_promised_qty_sql_lateral_where(self, warehouse):
        locations = warehouse.view_location_id
        sql = f"""
                m.id != move.id
                AND m.product_id = move.product_id
                AND p_type.code = 'outgoing'
                AND loc.parent_path LIKE ANY(%(location_paths)s)
                AND (
                    {self._previous_promised_qty_sql_moves_before()}
                    OR (
                        move.need_release IS true
                        AND ({self._previous_promised_qty_sql_moves_no_release()})
                    )
                )
                AND m.state IN (
                    'waiting', 'confirmed', 'partially_available', 'assigned'
                )
        """
        params = {
            "location_paths": [f"{location.parent_path}%" for location in locations]
        }
        horizon_date = self._promise_reservation_horizon_date()
        if horizon_date:
            sql += (
                " AND (m.need_release IS true AND m.date <= %(horizon)s "
                "      OR m.need_release IS false)"
            )
            params["horizon"] = horizon_date
        return sql, params

    def _previous_promised_qty_sql(self, warehouse):
        """Lookup query for product promised qty in the same warehouse.

        Moves to consider are either already released or still be to released
        but not done yet. Each of them should fit the reservation horizon.
        """
        params = {"move_ids": tuple(self.ids)}
        lateral_where, lateral_params = self._previous_promised_qty_sql_lateral_where(
            warehouse
        )
        params.update(lateral_params)
        query = self._previous_promised_qty_sql_main_query().format(
            lateral_where=lateral_where
        )
        return query, params

    def _group_by_warehouse(self):
        return groupby(self, lambda m: m.warehouse_id)

    def _get_previous_promised_qties(self):
        self.env.flush_all()
        self.env["stock.move.line"].flush_model(["move_id", "quantity"])
        self.env["stock.location"].flush_model(["parent_path"])
        previous_promised_qties = {}
        for warehouse, moves in self._group_by_warehouse():
            moves = self.browse().union(*moves)
            if not warehouse:
                for move in moves:
                    previous_promised_qties[move.id] = 0
                continue
            query, params = moves._previous_promised_qty_sql(warehouse)
            self.env.cr.execute(query, params)
            rows = dict(self.env.cr.fetchall())
            previous_promised_qties.update(rows)
        return previous_promised_qties

    # As we don't set depends here, we need to invalidate cache before
    # accessing the computed value.
    # This also apply to any computed field depending on this one
    @api.depends()
    def _compute_previous_promised_qty(self):
        if not self.ids:
            return
        previous_promised_qty_by_move = self._get_previous_promised_qties()
        for move in self:
            previous_promised_qty = previous_promised_qty_by_move.get(move.id, 0)
            move.previous_promised_qty = previous_promised_qty

    def _is_release_needed(self):
        self.ensure_one()
        return self.need_release and self.state not in ["done", "cancel"]

    def _is_release_ready(self):
        """Checks if a move itself is ready for release
        without considering the picking release_ready


        Be careful, when calling this method, you must ensure that the
        'ordered_available_to_promise_qty' field is up to date. If not,
        you should invalidate the cache before calling this method. This
        is not done automatically to avoid unnecessary cache invalidation
        and to allow batch computation. The `_is_release_ready` method
        is designed to be called on a single record. If we do the cache
        invalidation here, it would be done for each record, which means
        that the computation of the 'ordered_available_to_promise_qty'
        would be done for each record, which is not efficient.
        """
        self.ensure_one()
        if not self._is_release_needed() or self.state == "draft":
            return False
        release_policy = self.picking_id.release_policy
        rounding = self.product_id.uom_id.rounding
        ordered_available_to_promise_qty = self.ordered_available_to_promise_qty
        if release_policy == "one":
            return (
                float_compare(
                    ordered_available_to_promise_qty,
                    self.product_qty,
                    precision_rounding=rounding,
                )
                == 0
            )
        return (
            float_compare(
                ordered_available_to_promise_qty, 0, precision_rounding=rounding
            )
            > 0
        )

    def _get_release_ready_depends(self):
        return [
            "ordered_available_to_promise_qty",
            "picking_id.release_policy",
            "picking_id.move_ids",
            "need_release",
            "state",
        ]

    @api.depends(lambda self: self._get_release_ready_depends())
    def _compute_release_ready(self):
        self.invalidate_recordset(["ordered_available_to_promise_qty"])
        for move in self:
            release_ready = move._is_release_ready()
            if release_ready and move.picking_id.release_policy == "one":
                release_ready = move.picking_id.release_ready
            move.release_ready = release_ready

    def _search_release_ready(self, operator, value):
        if operator != "=":
            raise UserError(self.env._("Unsupported operator %s", operator))
        moves = self.search([("ordered_available_to_promise_uom_qty", ">", 0)])
        moves = moves.filtered(lambda m: m.release_ready)
        return [("id", "in", moves.ids)]

    def _get_ordered_available_to_promise_by_warehouse(self, warehouse):
        res = {}
        if not warehouse:
            for move in self:
                res[move] = {
                    "ordered_available_to_promise_uom_qty": 0,
                    "ordered_available_to_promise_qty": 0,
                }
            return res

        location_domain = warehouse.view_location_id._get_available_to_promise_domain()
        domain_quant = expression.AND(
            [[("product_id", "in", self.product_id.ids)], location_domain]
        )
        location_quants = self.env["stock.quant"].read_group(
            domain_quant, ["product_id", "quantity"], ["product_id"]
        )
        quants_available = {
            item["product_id"][0]: item["quantity"] for item in location_quants
        }
        for move in self:
            product_uom = move.product_id.uom_id
            previous_promised_qty = move.previous_promised_qty

            rounding = product_uom.rounding
            available_qty = float_round(
                quants_available.get(move.product_id.id, 0.0),
                precision_rounding=rounding,
            )

            real_promised = available_qty - previous_promised_qty
            uom_promised = product_uom._compute_quantity(
                real_promised,
                move.product_uom,
                rounding_method="HALF-UP",
            )
            res[move] = {
                "ordered_available_to_promise_uom_qty": max(
                    min(uom_promised, move.product_uom_qty), 0.0
                ),
                "ordered_available_to_promise_qty": max(
                    min(real_promised, move.product_qty), 0.0
                ),
            }
        return res

    def _get_ordered_available_to_promise(self):
        res = {}
        moves_by_warehouse = self._group_by_warehouse()
        # Compute On-Hand quantity (equivalent of qty_available) for all "view
        # locations" of all the warehouses: we may release as soon as we have
        # the quantity somewhere. Do not use "qty_available" to get a faster
        # computation.
        for warehouse, moves in moves_by_warehouse:
            moves = self.browse().union(*moves)
            res.update(moves._get_ordered_available_to_promise_by_warehouse(warehouse))
        return res

    @api.depends()
    def _compute_ordered_available_to_promise(self):
        moves = self.filtered(
            lambda move: move._should_compute_ordered_available_to_promise()
        )
        (self - moves).update(
            {
                "ordered_available_to_promise_qty": 0.0,
                "ordered_available_to_promise_uom_qty": 0.0,
            }
        )
        for move, values in moves._get_ordered_available_to_promise().items():
            move.update(values)

    def _search_ordered_available_to_promise_uom_qty(self, operator, value):
        operator_mapping = {
            "<": py_operator.lt,
            "<=": py_operator.le,
            ">": py_operator.gt,
            ">=": py_operator.ge,
            "=": py_operator.eq,
            "!=": py_operator.ne,
        }
        if operator not in operator_mapping:
            raise UserError(self.env._("Unsupported operator %s", operator))
        moves = self.search([("need_release", "=", True)])
        operator_func = operator_mapping[operator]
        # computed field has no depends set, invalidate cache before reading
        moves.invalidate_recordset(["ordered_available_to_promise_uom_qty"])
        moves = moves.filtered(
            lambda m: operator_func(m.ordered_available_to_promise_uom_qty, value)
        )
        return [("id", "in", moves.ids)]

    def _should_compute_ordered_available_to_promise(self):
        return (
            self.picking_code == "outgoing"
            and self.product_id.is_storable
            and not self.location_id.should_bypass_reservation()
        )

    def _action_cancel(self):
        if not self.env.context.get("from_merge_no_need_release"):
            # Unrelease moves that must be, before canceling them.
            # We skip this when merging moves that are all released.
            self.unrelease()
        super()._action_cancel()
        self.write({"need_release": False})
        return True

    def _promise_reservation_horizon(self):
        return self.env.company.sudo().stock_reservation_horizon

    def _promise_reservation_horizon_date(self):
        horizon = self._promise_reservation_horizon()
        if horizon:
            # start from end of today and add horizon days
            return date_utils.add(
                date_utils.end_of(fields.Datetime.today(), "day"), days=horizon
            )
        return None

    def release_available_to_promise(self):
        return self._run_stock_rule()

    def _prepare_move_split_vals(self, qty):
        vals = super()._prepare_move_split_vals(qty)
        # The method set procure_method as 'make_to_stock' by default on split,
        # but we want to keep 'make_to_order' for chained moves when we split
        # a partially available move in _run_stock_rule().
        if self.env.context.get("release_available_to_promise"):
            vals.update({"procure_method": self.procure_method, "need_release": True})
        return vals

    def _get_release_decimal_precision(self):
        return self.env["decimal.precision"].precision_get("Product Unit of Measure")

    def _get_release_remaining_qty(self):
        self.ensure_one()
        quantity = min(self.product_qty, self.ordered_available_to_promise_qty)
        remaining = self.product_qty - quantity
        precision = self._get_release_decimal_precision()
        if not float_compare(remaining, 0, precision_digits=precision) > 0:
            return
        return remaining

    def _prepare_procurement_values(self):
        res = super()._prepare_procurement_values()
        res["date_priority"] = self.date_priority
        return res

    def _run_stock_rule(self):
        """Launch procurement group run method with remaining quantity

        As we only generate chained moves for the quantity available minus the
        quantity promised to older moves, to delay the reservation at the
        latest, we have to periodically retry to assign the remaining
        quantities.
        """
        procurement_requests = []
        released_moves = self.env["stock.move"]
        # computed field depends on ordered_available_to_promise_qty that has no
        # depends set, invalidate cache before reading
        self.invalidate_recordset(["release_ready"])
        for move in self:
            if not move.release_ready:
                continue
            remaining_qty = move._get_release_remaining_qty()
            if remaining_qty:
                move._release_split(remaining_qty)
            released_moves |= move

        # Move the unreleased moves to a backorder.
        # This behavior can be disabled by setting the flag
        # no_backorder_at_release on the stock.route of the move.
        released_pickings = released_moves.picking_id
        unreleased_moves = released_pickings.move_ids - released_moves
        unreleased_moves_to_bo = unreleased_moves.filtered(
            lambda m: m.state not in ("done", "cancel")
            and m.need_release
            and not m.rule_id.no_backorder_at_release
        )
        if unreleased_moves_to_bo:
            unreleased_moves_to_bo._unreleased_to_backorder()

        # Pull the released moves
        for move in released_moves:
            move._before_release()
            values = move._prepare_procurement_values()
            values["move_dest_ids"] = move
            procurement_requests.append(
                self.env["procurement.group"].Procurement(
                    move.product_id,
                    move.product_uom_qty,
                    move.product_uom,
                    move.location_id,
                    move.rule_id and move.rule_id.name or "/",
                    move.origin,
                    move.company_id,
                    values,
                )
            )
        self.env["procurement.group"].run_defer(procurement_requests)

        assigned_moves = released_moves._after_release_assign_moves()
        assigned_moves._after_release_update_chain()

        # some moves may have been already released but not merged because of
        # an ongoing quantity on the pick step. Now that both are released, try
        # to merge them
        prereleased_moves = unreleased_moves.filtered(
            lambda m: m.state not in ("done", "cancel") and not m.need_release
        )
        if prereleased_moves:
            prereleased_moves._merge_moves()

        return assigned_moves

    def _before_release(self):
        """Hook that aims to be overridden."""
        self._release_set_expected_date()

    def _release_get_expected_date(self):
        """Return the new scheduled date of a single delivery move"""
        prep_time = self.env.company.stock_release_max_prep_time
        new_expected_date = fields.Datetime.add(
            fields.Datetime.now(), minutes=prep_time
        )
        return new_expected_date

    def _release_set_expected_date(self, new_expected_date=False):
        """Set scheduled date before releasing delivery moves

        This will be propagated to the chain of moves"""
        for move in self:
            if not new_expected_date:
                new_expected_date = move._release_get_expected_date()
            if not new_expected_date:
                continue
            move.date = new_expected_date

    def _after_release_update_chain(self):
        picking_ids = set()
        moves = self
        while moves:
            picking_ids.update(moves.picking_id.ids)
            moves = moves.move_orig_ids
        pickings = self.env["stock.picking"].browse(picking_ids)
        # Don't take into account pickings that are already done or canceled
        # This can happen if a move is a reliquat of a picking that has been
        # already been processed.
        pickings = pickings.filtered(lambda p: p.state not in ("done", "cancel"))
        pickings._after_release_update_chain()
        # Set the highest priority on all pickings in the chain
        priorities = pickings.mapped("priority")
        if priorities:
            pickings.write({"priority": max(priorities)})

    def _after_release_assign_moves(self):
        move_ids = []
        for origin_moves in self._get_chained_moves_iterator("move_orig_ids"):
            move_ids += origin_moves.filtered(
                lambda m: m.state not in ("cancel", "done")
            ).ids
        moves = self.browse(move_ids)
        moves._action_assign()
        return moves

    def _release_split(self, remaining_qty):
        """Split move and put remaining_qty to a backorder move."""
        new_move_vals = self.with_context(release_available_to_promise=True)._split(
            remaining_qty
        )
        new_move = self.create(new_move_vals)
        new_move._action_confirm(merge=False)
        return new_move

    def _unreleased_to_backorder(self):
        """Move the unreleased moves to a new backorder picking"""
        origin_pickings = {m.id: m.picking_id for m in self}
        self.with_context(release_available_to_promise=True)._assign_picking()
        backorder_links = {}
        for move in self:
            origin = origin_pickings[move.id]
            if origin:
                backorder_links[move.picking_id] = origin
        for backorder, origin in backorder_links.items():
            backorder._release_link_backorder(origin)

    def _assign_picking_post_process(self, new=False):
        res = super()._assign_picking_post_process(new)
        priorities = self.mapped("move_dest_ids.picking_id.priority")
        if priorities:
            self.picking_id.write({"priority": max(priorities)})
        return res

    def _get_chained_moves_iterator(self, chain_field):
        """Return an iterator on the moves of the chain.

        The iterator returns the moves in the order of the chain.
        The loop into the iterator is the current moves.
        """
        moves = self
        visited_moves = self.browse()
        while moves:
            yield moves
            visited_moves += moves
            moves = moves.mapped(chain_field) - visited_moves

    def _return_quantity_in_stock(self, qty_to_return_per_move):
        """Return a quantity from a list of moves.

        The quantity to return is in the product uom"""
        moves_to_return = self.browse([m_id for m_id in qty_to_return_per_move.keys()])
        moves_per_type = groupby(moves_to_return, lambda m: m.picking_type_id)
        for picking_type, moves_list in moves_per_type:
            moves = self.browse().union(*moves_list)
            pickings = moves.picking_id
            if not pickings:
                continue
            return_type = picking_type.return_picking_type_id
            wiz_values = {
                "picking_id": fields.first(pickings).id,
            }
            product_return_moves = []
            if not return_type:
                message = self.env._(
                    "The operation %(picking_names)s is done and cannot be returned",
                    picking_names=", ".join(pickings.mapped("name")),
                )
                raise UserError(message)
            for move in moves:
                # Cannot return an unprocessed move
                if move.state != "done":
                    continue
                product = move.product_id
                uom = product.uom_id
                qty_to_return = qty_to_return_per_move.get(move.id, 0)
                # Cannot return 0 qty
                if float_is_zero(qty_to_return, precision_rounding=uom.rounding):
                    continue
                return_move_vals = {
                    "product_id": product.id,
                    "quantity": qty_to_return,
                    "uom_id": uom.id,
                    "move_id": move.id,
                }
                product_return_moves.append((0, 0, return_move_vals))
            if product_return_moves:
                wiz_values["product_return_moves"] = product_return_moves
                location_id = return_type.default_location_dest_id.id
                return_wiz = (
                    self.env["stock.return.picking"]
                    .with_context(return_loc_dest_id=location_id)
                    .create(wiz_values)
                )

                action = return_wiz.action_create_returns()
                cancel_picking = self.picking_id.browse(action["res_id"])
                # Do not copy the responsible user from the source picking as somebody
                # else could scan the new cancel picking
                cancel_picking.user_id = False

                returned_moves = return_wiz.product_return_moves.move_id
                pickings_to_assign = returned_moves.move_dest_ids.picking_id.filtered(
                    lambda picking, cancel_picking=cancel_picking: picking.id
                    != cancel_picking.id
                    and picking.state == "confirmed"
                )
                if pickings_to_assign:
                    pickings_to_assign.action_assign()
        return True

    def _unrelease_set_returnable_qty_per_move(
        self, qty_to_return, qty_to_return_per_move
    ):
        returnable_qty = 0
        for move in self:
            rounding = move.product_id.uom_id.rounding
            # As a move might have multiple dest ids, we might have
            # already planned to return a few units already.
            # Get it, and deduce it from the returnable qty
            move_qty_planned = qty_to_return_per_move.get(move.id, 0)
            # A move might already have return moves linked to it, deduce their quantity
            move_returned_qty = sum(
                move.returned_move_ids.filtered(lambda m: m.state != "cancel").mapped(
                    "product_qty"
                )
            )
            move_returnable_qty = min(
                qty_to_return, move.product_qty - move_returned_qty - move_qty_planned
            )
            if float_is_zero(move_returnable_qty, precision_rounding=rounding):
                continue
            # Update the quantity
            qty_to_return_per_move[move.id] += move_returnable_qty
            qty_to_return -= move_returnable_qty
            returnable_qty += move_returnable_qty
            if float_is_zero(qty_to_return, precision_rounding=rounding):
                break
        return returnable_qty

    def unrelease(self, safe_unrelease=False):
        """Unrelease unreleasable moves

        If safe_unrelease is True, the unreleasaable moves for which the
        processing has already started will be ignored
        """
        moves_to_unrelease = self.filtered(lambda m: m._is_unreleaseable())
        if safe_unrelease:
            moves_to_unrelease = self.filtered("unrelease_allowed")
        forbidden_moves = moves_to_unrelease.filtered(lambda m: not m.unrelease_allowed)
        if forbidden_moves:
            forbidden_moves._unrelease_not_allowed_error()
        moves_to_unrelease.write({"need_release": True})

        qty_to_return_per_move = defaultdict(float)
        for move in moves_to_unrelease:
            rounding = move.product_id.uom_id.rounding
            # When a move is returned, it is going straight to WH/Stock,
            # skipping all intermediate zones (pick/pack).
            # That is why we need to keep track of qty returned along the way.
            # We do not want to return the same goods at each step.
            # At a given step (pick/pack/ship), qty to return is
            # move.product_uom_qty - cancelled_qty_at_step - already returned qties
            qty_to_unrelease = move.product_qty
            qty_returned_for_move = 0
            iterator = move._get_chained_moves_iterator("move_orig_ids")
            moves_to_cancel_for_move = self.env["stock.move"]
            # backup procure_method as when you don't propagate cancel, the
            # destination move is forced to make_to_stock
            procure_method = move.procure_method
            next(iterator)  # skip the current move
            for origin_moves in iterator:
                qty_to_cancel = qty_to_unrelease - qty_returned_for_move
                if float_is_zero(qty_to_cancel, precision_rounding=rounding):
                    break
                todo_origin_moves = origin_moves.filtered(
                    lambda m: m.state not in ("done", "cancel")
                )
                qty_canceled = 0
                if todo_origin_moves:
                    moves_to_cancel = move._split_origins(
                        todo_origin_moves, qty=qty_to_cancel
                    )
                    # avoid to propagate cancel to the original move
                    moves_to_cancel.write({"propagate_cancel": False})
                    moves_to_cancel_for_move |= moves_to_cancel
                    qty_canceled = sum(moves_to_cancel.mapped("product_qty"))
                # checking that for the current step (pick/pack/ship)
                # move.product_uom_qty == step.cancelled_qty + move.returned_quanty
                # If not the case, we have to move back goods in stock.
                qty_to_return = qty_to_cancel - qty_canceled
                done_moves = origin_moves.filtered(lambda m: m.state == "done")
                # in case of canceled origin_moves, the quantity to return must
                # be limited to the quantity not consumed
                done_dest_moves = done_moves.move_dest_ids.filtered(
                    lambda m: m.state == "done"
                )
                returnable_qty = sum(done_moves.mapped("quantity")) - sum(
                    done_dest_moves.mapped("quantity")
                )
                qty_to_return = min(qty_to_return, returnable_qty)
                if float_compare(qty_to_return, 0, precision_rounding=rounding) <= 0:
                    continue
                if not move.rule_id.allow_unrelease_return_done_move:
                    # Without allow_unrelease_return_done_move enabled,
                    # only moves that aren't done can be unreleased.
                    msg_args = {
                        "move_name": move.name,
                        "done_move_names": ", ".join(done_moves.mapped("name")),
                    }
                    message = self.env._(
                        (
                            "You cannot unrelease the move %(move_name)s "
                            "because some origin moves %(done_move_names)s are done"
                        ),
                        **msg_args,
                    )
                    raise UserError(message)
                # Multiple pickings can satisfy a move
                # -> len(move.move_orig_ids.picking_id) > 1
                # Group done_moves per picking, and create returns
                returnable_qty = done_moves._unrelease_set_returnable_qty_per_move(
                    qty_to_return, qty_to_return_per_move
                )
                qty_returned_for_move += returnable_qty

            moves_to_cancel_for_move._action_cancel()
            # restore the procure_method overwritten by _action_cancel()
            move.procure_method = procure_method
            move._recompute_state()
        self._return_quantity_in_stock(qty_to_return_per_move)
        moves_to_unrelease.write({"need_release": True})
        for picking, moves in itertools.groupby(
            moves_to_unrelease, lambda m: m.picking_id
        ):
            if not picking:
                continue
            move_names = "\n".join([m.display_name for m in moves])
            body = self.env._(
                "The following moves have been un-released: \n%(move_names)s",
                move_names=move_names,
            )
            picking.message_post(body=body)
            picking.last_release_date = False

    def _split_origins(self, origins, qty=None):
        """Split the origins of the move according to the quantity into the
        move and the quantity in the origin moves.

        Return the origins for the move's quantity.
        """
        self.ensure_one()
        if not qty:
            qty = self.product_qty
        # Unreserve goods before the split
        origins._do_unreserve()
        rounding = self.product_uom.rounding
        new_origin_moves = self.env["stock.move"]
        while float_compare(qty, 0, precision_rounding=rounding) > 0 and origins:
            origin = fields.first(origins)
            if float_compare(qty, origin.product_qty, precision_rounding=rounding) >= 0:
                qty -= origin.product_qty
                new_origin_moves |= origin
            else:
                new_move_vals = origin._split(qty)
                new_origin_moves |= self.create(new_move_vals)
                break
            origins -= origin
        # And then do the reservation again
        origins._action_assign()
        new_origin_moves._action_assign()
        return new_origin_moves

    def _search_picking_for_assignation_domain(self):
        domain = super()._search_picking_for_assignation_domain()
        if self.env.context.get("release_available_to_promise"):
            force_new_picking = not self.rule_id.no_backorder_at_release
            if force_new_picking:
                # We want a newer picking, search with '>' to prevent to select
                # any old available picking
                domain = expression.AND([domain, [("id", ">", self.picking_id.id)]])
        if self.picking_type_id.prevent_new_move_after_release:
            domain = expression.AND([domain, [("last_release_date", "=", False)]])
        return domain

    def _get_new_picking_values(self):
        values = super()._get_new_picking_values()
        # In v18, 'move_type' is no longer provided in values by default,
        # so we retrieve it from the group instead.
        move_type = (
            fields.first(self.group_id).move_type
            or fields.first(self.picking_type_id).move_type
            or "direct"
        )
        values["release_policy"] = move_type
        return values

    def write(self, vals):
        released_moves = self.browse()
        if (
            self.env.context.get("from_merge_need_release")
            and "product_uom_qty" in vals
        ):
            # when a move is merged, we need to unrelease it if the quantity
            # is changed and the move is unreleasable
            released_moves = self.filtered(lambda m: m._is_unreleaseable())
            # a change on the product_uom_qty on a released move with quantity
            # partially done should not be possible. The 'safe_unrelease' flag
            # is set to False to ensure this case is checked. Nevertheless,
            # we should never reach this point as the merge candidates are
            # filtered out in the method _update_candidate_moves_list to never
            # merge releaseable moves with partially done quantity.
            released_moves.unrelease(safe_unrelease=False)
        ret = super().write(vals)
        if released_moves:
            released_moves.release_available_to_promise()
        return ret

    def _is_mergeable(self):
        self.ensure_one()
        return self.state not in ("draft", "done", "cancel") and (
            self.need_release or self.unrelease_allowed
        )

    def _prepare_merge_moves_distinct_fields(self):
        fields = super()._prepare_merge_moves_distinct_fields()
        if self.env.context.get("from_merge_no_need_release"):
            # when we merge moves that do not need release, ensure candidates
            # have the same value for need release (i.e. False)
            fields.append("need_release")
        return fields

    def _update_candidate_moves_list(self, candidate_moves):
        # candidate_moves is a list of recordset of moves
        # it contains one recordset per move to merge
        # each recordset contains the moves that we want to merge (an item of self)
        # and the candidate moves to merge into
        res = super()._update_candidate_moves_list(candidate_moves)
        if not self.env.context.get("from_merge_need_release"):
            return res
        # when merging a move that needs release, filter out the moves that are
        # not unreleasable
        new_candidate_moves = [
            candidates.filtered(
                lambda m, moves_to_merge=self: m in moves_to_merge or m._is_mergeable()
            )
            for candidates in candidate_moves
        ]
        # clear and update the candidate set
        candidate_moves.clear()
        candidate_moves.update(new_candidate_moves)
        return res

    def _merge_moves(self, merge_into=False):
        res = self.browse()
        no_need_release = self.filtered(lambda m: not m.need_release)
        if no_need_release:
            # For moves that do not need release, search moves that also do not
            # need release
            from_merge_no_need_release = self.env.context.get(
                "from_merge_no_need_release", False
            )
            res |= (
                super(
                    StockMove,
                    no_need_release.with_context(from_merge_no_need_release=True),
                )
                ._merge_moves(merge_into=merge_into)
                .with_context(from_merge_no_need_release=from_merge_no_need_release)
            )
        need_release = self - no_need_release
        if need_release:
            # For moves that do need release, search moves that also need
            # release or are unreleasable
            from_merge_need_release = self.env.context.get(
                "from_merge_need_release", False
            )
            if merge_into:
                merge_into = merge_into.filtered(lambda m: m._is_mergeable())
            res |= (
                super(
                    StockMove, need_release.with_context(from_merge_need_release=True)
                )
                ._merge_moves(merge_into=merge_into)
                .with_context(from_merge_need_release=from_merge_need_release)
            )
        return res
