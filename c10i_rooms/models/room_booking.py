from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from itertools import groupby
from operator import attrgetter


class RoomBooking(models.Model):
    _name = "room.booking"
    _inherit = ["mail.thread"]
    _description = "Room Booking"
    _order = "start_datetime desc, id"

    name = fields.Char(string="Booking Name", required=True, tracking=True)
    room_id = fields.Many2one(
        "room.room",
        string="Room",
        required=True,
        ondelete="cascade",
        group_expand="_read_group_room_id",
        tracking=True,
    )
    start_datetime = fields.Datetime(string="Start Datetime", required=True, tracking=True)
    stop_datetime = fields.Datetime(string="End Datetime", required=True, tracking=True)
    organizer_id = fields.Many2one(
        "res.users",
        string="Organizer",
        default=lambda self: self.env.user,
        tracking=True,
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    @api.constrains("start_datetime", "stop_datetime")
    def _check_date_boundaries(self):
        for booking in self:
            if booking.start_datetime >= booking.stop_datetime:
                raise ValidationError(
                    _("The start date of %s must be earlier than the end date.") % booking.name
                )

    @api.constrains("start_datetime", "stop_datetime")
    def _check_unique_slot(self):
        for booking in self:
            overlap = self.search([
                ("room_id", "=", booking.room_id.id),
                ("id", "!=", booking.id),
                ("start_datetime", "<", booking.stop_datetime),
                ("stop_datetime", ">", booking.start_datetime),
            ])
            if overlap:
                raise ValidationError(
                    _("Room %s is already booked during the selected time slot.") % booking.room_id.name
                )

    @api.model_create_multi
    def create(self, vals_list):
        bookings = super(RoomBooking, self).create(vals_list)
        # Notify frontend views of new bookings
        bookings_by_room = {}
        for room, group in groupby(sorted(bookings, key=attrgetter("room_id")), key=attrgetter("room_id")):
            bookings_by_room[room] = list(group)
        for room, booking_list in bookings_by_room.items():
            room._notify_booking_view("create", booking_list)
        return bookings

    def unlink(self):
        # Notify frontend of deleted bookings
        bookings_by_room = {}
        for room, group in groupby(sorted(self, key=attrgetter("room_id")), key=attrgetter("room_id")):
            bookings_by_room[room] = list(group)
        for room, booking_list in bookings_by_room.items():
            room._notify_booking_view("delete", booking_list)
        return super(RoomBooking, self).unlink()

    def write(self, vals):
        # Group existing bookings by room before write
        bookings_by_room = {}
        for room, group in groupby(sorted(self, key=attrgetter("room_id")), key=attrgetter("room_id")):
            bookings_by_room[room] = list(group)

        res = super(RoomBooking, self).write(vals)

        if "room_id" in vals:
            new_room = self.env["room.room"].browse(vals["room_id"])
            for room, booking_list in bookings_by_room.items():
                room._notify_booking_view("delete", booking_list)
                new_room._notify_booking_view("create", booking_list)
        elif {"name", "start_datetime", "stop_datetime"} & set(vals.keys()):
            for room, booking_list in bookings_by_room.items():
                room._notify_booking_view("update", booking_list)

        return res

    @api.model
    def _read_group_room_id(self, rooms, domain, order="office_id, name"):
        if self.env.context.get("room_booking_gantt_show_all_rooms"):
            return rooms.search([], order=order)
        return rooms

    @api.model
    def get_empty_list_help(self, help_message):
        result_help_message = super(RoomBooking, self).get_empty_list_help(help_message)
        if self.env.user.has_group("room.group_room_manager") and not self.env["room.room"].search_count([]):
            result_help_message += (
                '<a class="btn btn-outline-primary" href="/odoo/rooms/meeting-rooms/new">%s</a>'
                % _("Create a Room")
            )
        return result_help_message
