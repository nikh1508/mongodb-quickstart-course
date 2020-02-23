from data.owners import Owner
from data.cages import Cage
from data.bookings import Booking
from data.snakes import Snake
import datetime
import bson
from typing import List, Optional
from mongoengine.queryset.visitor import Q

def create_account(name: str, email: str) -> Owner:
    owner  = Owner()
    owner.name = name
    owner.email = email 
    owner.save()
    return owner

def find_account_by_email(email: str):
    owner = Owner.objects().filter(email=email).first()
    return owner

def register_cage(active_account: Owner, name, allow_dangerous, has_toys, carpeted, metres, price) -> Cage:
    cage = Cage()

    cage.name = name
    cage.square_metres = metres
    cage.is_carpeted = carpeted
    cage.has_toys = has_toys
    cage.allow_dangerous_snakes = allow_dangerous
    cage.price = price

    cage.save()
    active_account.cage_ids.append(cage.id)
    active_account.save()
    return cage

def find_cages_for_user(user: Owner):
    query = Cage.objects().filter(id__in=user.cage_ids)
    cages = list(query)

    return query    

def add_available_date( selected_cage, start_date, days):
    booking = Booking()
    booking.check_in_date = start_date
    booking.check_out_date = start_date + datetime.timedelta(days=days)

    cage = Cage.objects(id=selected_cage.id).first()
    cage.bookings.append(booking)
    cage.save()


def add_snake(account, name, length, species, is_venomous) -> Snake:
    snake = Snake()
    snake.name = name
    snake.length = length
    snake.species = species
    snake.is_venomous = is_venomous
    snake.save()

    owner = find_account_by_email(account.email)
    owner.snake_ids.append(snake.id)
    owner.save()

    return snake


def get_snakes_for_user(user_id: bson.ObjectId) -> List[Snake]:
    owner = Owner.objects(id=user_id).first()
    snakes = Snake.objects(id__in=owner.snake_ids).all()

    return list(snakes)

def get_available_cages(checkin: datetime.datetime, checkout: datetime.datetime, snake:Snake) -> List[Cage]:
    min_size = snake.length /4.
    
    query = Cage.objects(Q(square_metres__gte=min_size) & Q(bookings__check_in_date__lte=checkin) & Q(bookings__check_out_date__gte=checkout))

    if snake.is_venomous:
        query = query.filter(allow_dangerous_snakes=True)
    
    _cages = query.order_by('price', '-square_metres')
    _cages = list(_cages)
    cages = []

    for c in _cages:
        for b in c.bookings:
            if b.guest_snake_id is None:
                cages.append(c)
                break
    
    return cages


def book_cage(account, snake, cage, checkin, checkout):
    booking: Optional[Booking] = None

    for b in cage.bookings:
        if b.check_in_date <= checkin and b.check_out_date >= checkout and b.guest_snake_id is None:
            booking = b
            break

    booking.guest_owner_id = account.id
    booking.guest_snake_id = snake.id
    booking.check_in_date = checkin
    booking.check_out_date = checkout
    booking.booked_date = datetime.datetime.now()

    cage.save()


def get_bookings_for_user(email: str) -> List[Booking]:
    account = find_account_by_email(email)

    booked_cages = Cage.objects() \
        .filter(bookings__guest_owner_id=account.id) \
        .only('bookings', 'name')

    def map_cage_to_booking(cage, booking):
        booking.cage = cage
        return booking

    bookings = [
        map_cage_to_booking(cage, booking)
        for cage in booked_cages
        for booking in cage.bookings
        if booking.guest_owner_id == account.id
    ]

    return bookings
