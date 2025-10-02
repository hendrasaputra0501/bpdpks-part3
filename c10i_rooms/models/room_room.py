from uuid import uuid4
from odoo import models, fields, api


class Room(models.Model):
    _name = 'room.room'
    _inherit = ['mail.thread']
    _description = 'Room'
    _order = 'name'


    name = fields.Char('Room Name', required=True, tracking=True)
    active = fields.Boolean('Active', default=True)
    description = fields.Text('Description', help='Description of the room')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    room_booking_ids = fields.One2many('room.booking', 'room_id', string='Bookings')
    short_code = fields.Char("Short Code", default=lambda self: str(uuid4())[:8], copy=False, required=True, tracking=1)

    access_token = fields.Char("Access Token", default=lambda self: str(uuid4()), copy=False, readonly=True, required=True)
    is_available = fields.Boolean('Is Available', compute='_compute_is_available', store=True)
    next_booking_start = fields.Datetime('Next Booking Start', compute='_compute_next_booking_start', store=True)
    room_booking_url = fields.Char('Room Link', compute='_compute_room_booking_url')

    bookable_background_color = fields.Char("Available Background Color", default="#83c5be")
    booked_background_color = fields.Char("Booked Background Color", default="#dd2d4a")
    room_booking_image = fields.Image('Background Image')


    @api.depends('room_booking_ids')
    def _compute_is_available(self):
        RoomBooking = self.env['room.booking']
        for room in self:
            # Cari booking aktif untuk room ini
            active_bookings = RoomBooking.search([
                ('room_id', '=', room.id),
                ('start_datetime', '<=', fields.Datetime.now()),
                ('stop_datetime', '>=', fields.Datetime.now()),
            ])
            room.is_available = not bool(active_bookings)


    @api.depends("is_available", "room_booking_ids")
    def _compute_next_booking_start(self):
        now = fields.Datetime.now()
        for room in self:
            if room.is_available:
                next_booking = self.env["room.booking"].search(
                    [("room_id", "=", room.id), ("start_datetime", ">", now)],
                    order="start_datetime asc",
                    limit=1,
                )
                room.next_booking_start = next_booking.start_datetime or False
            else:
                room.next_booking_start = False

    @api.depends("short_code")
    def _compute_room_booking_url(self):
        for room in self:
            room.room_booking_url = f"{room.get_base_url()}/room/{room.short_code}/book"


    def _notify_booking_view(self, method, bookings=False):
        """The room booking page is meant to be used on a 'static' device (such
        as a tablet) and is not expected to be reloaded manually. We thus need
        a way to notify the frontend page of any change inside the room
        configuration (in which case we reload the view to apply those changes)
        or any booking update.
        """
        self.ensure_one()
        bus = self.env["bus.bus"]

        if method == "reload":
            bus.sendone(
                f"room_booking#{self.access_token}",
                {
                    "channel": f"room#{self.id}/reload",
                    "data": self.room_booking_url,
                },
            )
        elif method in ["create", "delete", "update"]:
            bus.sendone(
                f"room_booking#{self.access_token}",
                {
                    "channel": f"room#{self.id}/booking/{method}",
                    "data": [
                        {
                            "id": booking.id,
                            "name": booking.name,
                            "start_datetime": booking.start_datetime,
                            "stop_datetime": booking.stop_datetime,
                        }
                        for booking in (bookings or [])
                    ],
                },
            )
        else:
            raise NotImplementedError(
                f"Method '{method}' is not implemented for '_notify_booking_view'"
            )
