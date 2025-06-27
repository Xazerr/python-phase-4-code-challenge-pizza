#!/usr/bin/env python3
import os

from flask import Flask, request, jsonify
from flask_migrate import Migrate
from models import db, Restaurant, Pizza, RestaurantPizza

# ─── App & Database Configuration ──────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_URL = os.environ.get(
    "DB_URI",
    f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"
)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"]     = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False    # pretty-print JSON

db.init_app(app)
migrate = Migrate(app, db)

# ─── Home Route ───────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return "<h1>Pizza Restaurants API</h1>"

# ─── 1) GET /restaurants ───────────────────────────────────────────────────────
@app.route("/restaurants")
def list_restaurants():
    restaurant_list = Restaurant.query.all()
    restaurant_data = [
        restaurant_record.to_dict(only=("id", "name", "address"))
        for restaurant_record in restaurant_list
    ]
    return jsonify(restaurant_data)

# ─── 2) GET /restaurants/<id> ──────────────────────────────────────────────────
@app.route("/restaurants/<int:restaurant_id>")
def show_restaurant(restaurant_id):
    found_restaurant = Restaurant.query.get(restaurant_id)
    if not found_restaurant:
        return jsonify({"error": "Restaurant not found"}), 404

    # Manually build the JSON, one level deep, including pizza details
    result = {
        "id":      found_restaurant.id,
        "name":    found_restaurant.name,
        "address": found_restaurant.address,
        "restaurant_pizzas": []
    }

    for association_entry in found_restaurant.restaurant_pizzas:
        result["restaurant_pizzas"].append({
            "id":            association_entry.id,
            "price":         association_entry.price,
            "pizza_id":      association_entry.pizza_id,
            "restaurant_id": association_entry.restaurant_id,
            # include nested pizza object so rp.pizza.name exists in the frontend
            "pizza": {
                "id":          association_entry.pizza.id,
                "name":        association_entry.pizza.name,
                "ingredients": association_entry.pizza.ingredients
            }
        })

    return jsonify(result)

# ─── 3) DELETE /restaurants/<id> ───────────────────────────────────────────────
@app.route("/restaurants/<int:restaurant_id>", methods=["DELETE"])
def remove_restaurant(restaurant_id):
    found_restaurant = Restaurant.query.get(restaurant_id)
    if not found_restaurant:
        return jsonify({"error": "Restaurant not found"}), 404

    db.session.delete(found_restaurant)
    db.session.commit()
    return ("", 204)

# ─── 4) GET /pizzas ─────────────────────────────────────────────────────────────
@app.route("/pizzas")
def list_pizzas():
    pizza_list = Pizza.query.all()
    pizza_data = [
        pizza_record.to_dict(only=("id", "name", "ingredients"))
        for pizza_record in pizza_list
    ]
    return jsonify(pizza_data)

# ─── 5) POST /restaurant_pizzas ────────────────────────────────────────────────
@app.route("/restaurant_pizzas", methods=["POST"])
def add_restaurant_pizza():
    request_data = request.get_json()

    try:
        new_association = RestaurantPizza(
            price=request_data["price"],
            pizza_id=request_data["pizza_id"],
            restaurant_id=request_data["restaurant_id"]
        )
        db.session.add(new_association)
        db.session.commit()

    except ValueError:
        return jsonify({"errors": ["validation errors"]}), 400

    except Exception as generic_error:
        return jsonify({"errors": [str(generic_error)]}), 400

    created_entry = {
        "id":            new_association.id,
        "price":         new_association.price,
        "pizza_id":      new_association.pizza_id,
        "restaurant_id": new_association.restaurant_id,
        "pizza": {
            "id":          new_association.pizza.id,
            "name":        new_association.pizza.name,
            "ingredients": new_association.pizza.ingredients
        },
        "restaurant": {
            "id":      new_association.restaurant.id,
            "name":    new_association.restaurant.name,
            "address": new_association.restaurant.address
        }
    }

    return jsonify(created_entry), 201

# ─── Run the Server ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(port=5555, debug=True)



