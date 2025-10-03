"""Host API endpoints."""

import ipaddress

from flask import request
from flask_restx import Namespace, Resource, fields

from ipam.extensions import db
from ipam.models import Host, Network
from ipam.api.models import (
    host_model,
    host_input_model,
    pagination_model,
    error_model,
)

api = Namespace("hosts", description="Host management operations")

# Register models
host = api.model("Host", host_model)
host_input = api.model("HostInput", host_input_model)
pagination = api.model("Pagination", pagination_model)
error = api.model("Error", error_model)

# Paginated response model
host_list = api.model(
    "HostList",
    {
        "data": fields.List(fields.Nested(host)),
        "pagination": fields.Nested(pagination),
    },
)


@api.route("")
class HostList(Resource):
    @api.doc("list_hosts")
    @api.marshal_with(host_list)
    @api.param("page", "Page number", type=int, default=1)
    @api.param("per_page", "Items per page", type=int, default=50)
    @api.param("hostname", "Filter by hostname (wildcard supported)")
    @api.param("cname", "Filter by CNAME")
    @api.param("status", "Filter by status (active, inactive, reserved)")
    @api.param("mac_address", "Filter by MAC address")
    @api.param("network_id", "Filter by network ID", type=int)
    def get(self):
        """List all hosts with optional filtering."""
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)

        query = Host.query

        # Apply filters
        if hostname := request.args.get("hostname"):
            query = query.filter(Host.hostname.ilike(f"%{hostname}%"))
        if cname := request.args.get("cname"):
            query = query.filter(Host.cname.ilike(f"%{cname}%"))
        if status := request.args.get("status"):
            query = query.filter(Host.status == status)
        if mac_address := request.args.get("mac_address"):
            query = query.filter(Host.mac_address == mac_address)
        if network_id := request.args.get("network_id", type=int):
            query = query.filter(Host.network_id == network_id)

        # Paginate results
        pagination_obj = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        return {
            "data": [
                {
                    "id": h.id,
                    "ip_address": h.ip_address,
                    "hostname": h.hostname,
                    "cname": h.cname,
                    "mac_address": h.mac_address,
                    "status": h.status,
                    "description": h.description,
                    "network_id": h.network_id,
                    "network": (
                        f"{h.network_ref.network}/{h.network_ref.cidr}"
                        if h.network_ref
                        else None
                    ),
                }
                for h in pagination_obj.items
            ],
            "pagination": {
                "page": pagination_obj.page,
                "per_page": pagination_obj.per_page,
                "total_items": pagination_obj.total,
                "total_pages": pagination_obj.pages,
            },
        }

    @api.doc("create_host")
    @api.expect(host_input, validate=True)
    @api.marshal_with(host, code=201)
    @api.response(400, "Validation Error", error)
    def post(self):
        """Create a new host."""
        data = request.json

        # Validate IP address
        try:
            ipaddress.IPv4Address(data["ip_address"])
        except ValueError as e:
            api.abort(400, f"Invalid IP address: {e}")

        # Check for duplicate
        existing = Host.query.filter_by(ip_address=data["ip_address"]).first()
        if existing:
            api.abort(400, "IP address already exists")

        # Auto-detect network if not provided
        network_id = data.get("network_id")
        if not network_id:
            networks = Network.query.all()
            for net in networks:
                net_obj = ipaddress.IPv4Network(
                    f"{net.network}/{net.cidr}", strict=False
                )
                if ipaddress.IPv4Address(data["ip_address"]) in net_obj:
                    network_id = net.id
                    break

        # Create host
        host_obj = Host(
            ip_address=data["ip_address"],
            hostname=data.get("hostname"),
            cname=data.get("cname"),
            mac_address=data.get("mac_address"),
            status=data.get("status", "active"),
            description=data.get("description"),
            network_id=network_id,
        )

        db.session.add(host_obj)
        db.session.commit()

        return {
            "id": host_obj.id,
            "ip_address": host_obj.ip_address,
            "hostname": host_obj.hostname,
            "cname": host_obj.cname,
            "mac_address": host_obj.mac_address,
            "status": host_obj.status,
            "description": host_obj.description,
            "network_id": host_obj.network_id,
            "network": (
                f"{host_obj.network_ref.network}/{host_obj.network_ref.cidr}"
                if host_obj.network_ref
                else None
            ),
        }, 201


@api.route("/<int:id>")
@api.param("id", "The host identifier")
class HostResource(Resource):
    @api.doc("get_host")
    @api.marshal_with(host)
    @api.response(404, "Host not found")
    def get(self, id):
        """Get a specific host by ID."""
        host_obj = Host.query.get_or_404(id)
        return {
            "id": host_obj.id,
            "ip_address": host_obj.ip_address,
            "hostname": host_obj.hostname,
            "cname": host_obj.cname,
            "mac_address": host_obj.mac_address,
            "status": host_obj.status,
            "description": host_obj.description,
            "network_id": host_obj.network_id,
            "network": (
                f"{host_obj.network_ref.network}/{host_obj.network_ref.cidr}"
                if host_obj.network_ref
                else None
            ),
        }

    @api.doc("update_host")
    @api.expect(host_input, validate=True)
    @api.marshal_with(host)
    @api.response(404, "Host not found")
    @api.response(400, "Validation Error", error)
    def put(self, id):
        """Update a host."""
        host_obj = Host.query.get_or_404(id)
        data = request.json

        # Validate IP address if changed
        if data["ip_address"] != host_obj.ip_address:
            try:
                ipaddress.IPv4Address(data["ip_address"])
            except ValueError as e:
                api.abort(400, f"Invalid IP address: {e}")

            # Check for duplicate
            existing = (
                Host.query.filter_by(ip_address=data["ip_address"])
                .filter(Host.id != id)
                .first()
            )
            if existing:
                api.abort(400, "IP address already exists")

        # Auto-detect network if IP changed and network_id not provided
        network_id = data.get("network_id", host_obj.network_id)
        if data["ip_address"] != host_obj.ip_address and not data.get(
            "network_id"
        ):
            networks = Network.query.all()
            network_id = None
            for net in networks:
                net_obj = ipaddress.IPv4Network(
                    f"{net.network}/{net.cidr}", strict=False
                )
                if ipaddress.IPv4Address(data["ip_address"]) in net_obj:
                    network_id = net.id
                    break

        # Update fields
        host_obj.ip_address = data["ip_address"]
        host_obj.hostname = data.get("hostname")
        host_obj.cname = data.get("cname")
        host_obj.mac_address = data.get("mac_address")
        host_obj.status = data.get("status", "active")
        host_obj.description = data.get("description")
        host_obj.network_id = network_id

        db.session.commit()

        return {
            "id": host_obj.id,
            "ip_address": host_obj.ip_address,
            "hostname": host_obj.hostname,
            "cname": host_obj.cname,
            "mac_address": host_obj.mac_address,
            "status": host_obj.status,
            "description": host_obj.description,
            "network_id": host_obj.network_id,
            "network": (
                f"{host_obj.network_ref.network}/{host_obj.network_ref.cidr}"
                if host_obj.network_ref
                else None
            ),
        }

    @api.doc("delete_host")
    @api.response(204, "Host deleted")
    @api.response(404, "Host not found")
    def delete(self, id):
        """Delete a host."""
        db, Host, _ = get_models()
        host_obj = Host.query.get_or_404(id)

        db.session.delete(host_obj)
        db.session.commit()

        return "", 204
