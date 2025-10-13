from odoo import http
from odoo.http import request, Response
import json

class RoomApi(http.Controller):
    @http.route('/api/rooms', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_rooms(self, **kwargs):
        rooms = request.env['room.room'].sudo().search([])
        data = [
            {
                "id": r.id, 
                "name": r.name, 
                "short_code": r.short_code,
                "description": r.description,
                "room_booking_url": r.room_booking_url,
                "next_booking_start": str(r.next_booking_start),
                "is_available": r.is_available,
                "bookings": [
                    {
                        "id": b.id,
                        "name": b.name,
                        "room_id": b.room_id.id,
                        "organizer_id": b.organizer_id.name,
                        "start_datetime": str(b.start_datetime),
                        "stop_datetime": str(b.stop_datetime),
                    }
                    for b in r.room_booking_ids
                ] 
            } for r in rooms
        ]
        return request.make_response(
            json.dumps({"datas": data}),
            headers=[
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*')
            ]
        )


    @http.route('/api/rooms/<int:room_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_room(self, room_id, **kwargs):
        rooms = request.env['room.room'].sudo().browse(room_id)
        if not rooms.exists():
            return Response(json.dumps({'message': 'Room not found with id {}'.format(room_id)}),
                            content_type='application/json', status=404)

        data = [
            {
                "id": r.id, 
                "name": r.name, 
                "short_code": r.short_code,
                "description": r.description,
                "room_booking_url": r.room_booking_url,
                "next_booking_start": str(r.next_booking_start),
                "is_available": r.is_available,
                "bookings": [
                    {
                        "id": b.id,
                        "name": b.name,
                        "room_id": b.room_id.id,
                        "organizer_id": b.organizer_id.name,
                        "start_datetime": str(b.start_datetime),
                        "stop_datetime": str(b.stop_datetime),
                    }
                    for b in r.room_booking_ids
                ] 
            } for r in rooms
        ]

        return request.make_response(
            json.dumps({"data": data}),
            headers=[('Content-Type', 'application/json')]
        )