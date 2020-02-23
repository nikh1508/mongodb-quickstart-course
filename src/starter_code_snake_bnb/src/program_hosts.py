from colorama import Fore
from infrastructure.switchlang import switch
from dateutil import parser
import infrastructure.state as state
import services.data_services as svc 
import datetime

def run():
    print(' ****************** Welcome host **************** ')
    print()

    show_commands()

    while True:
        action = get_action()

        with switch(action) as s:
            s.case('c', create_account)
            s.case('a', log_into_account)
            s.case('l', list_cages)
            s.case('r', register_cage)
            s.case('u', update_availability)
            s.case('v', view_bookings)
            s.case('m', lambda: 'change_mode')
            s.case(['x', 'bye', 'exit', 'exit()'], exit_app)
            s.case('?', show_commands)
            s.case('', lambda: None)
            s.default(unknown_command)

        if action:
            print()

        if s.result == 'change_mode':
            return


def show_commands():
    print('What action would you like to take:')
    print('[C]reate an account')
    print('Login to your [a]ccount')
    print('[L]ist your cages')
    print('[R]egister a cage')
    print('[U]pdate cage availability')
    print('[V]iew your bookings')
    print('Change [M]ode (guest or host)')
    print('e[X]it app')
    print('[?] Help (this info)')
    print()


def create_account():
    print(' ****************** REGISTER **************** ')
    name = input('Your Name? :')
    email = input('Your e-mail? :')
    old_account = svc.find_account_by_email(email)
    if old_account:
        error_msg(f"ERROR: Account with this email {email} already exists.")
        return
    state.active_account = svc.create_account(name, email)
    success_msg(f"Account created with account id {state.active_account.id}")

def log_into_account():
    print(' ****************** LOGIN **************** ')

    email = input('E-mail? :')
    owner = svc.find_account_by_email(email)
    if not owner:
        error_msg(f'No account exists by e-mail address :{email}')
        return
    success_msg('Logged In')
    state.active_account = owner


def register_cage():
    print(' ****************** REGISTER CAGE **************** ')

    if not state.active_account:
        error_msg('You must login first in order to register a cage')
        return
    meters = input('Area(Sq. Metres)? :')
    if not meters:
        error_msg('Cancelled')
        return
    meters = float(meters)
    carpeted = input('Is it carpeted [y,n]? :').lower().startswith('y')
    has_toys = input('Have snake toys [y,n]? :').lower().startswith('y')
    allow_dangerous=input('Can you host a venomous snake [y,n]? :').lower().startswith('y')
    name = input('Name for the Cage? :')
    price = float(input('Price for cage? :'))

    cage = svc.register_cage(state.active_account, name, allow_dangerous, has_toys, carpeted, meters, price)
    state.reload_account()
    success_msg(f'Registered a new cage with new cage-id: {cage.id}')


def list_cages(supress_header=False):
    if not supress_header:
        print(' ******************     Your cages     **************** ')

    if not state.active_account:
        error_msg('You must login first in order to register a cage')
        return
    cages = svc.find_cages_for_user(state.active_account)
    if len(cages) == 0:
        error_msg("You don't have any cages")
    else:
        success_msg(f'You have {len(cages)} Cages.')
    for i, c in enumerate(cages):
        print(f'\t{i+1}. {c.name} : {c.square_metres} Sq. Metres')
        for b in c.bookings:
            print(f'\t\t* Availability | Start Date : {b.check_in_date}\tEnd Date : {b.check_out_date} | Booked :{"Yes" if b.booked_date is not None else "No"}')


def update_availability():
    print(' ****************** Add available date **************** ')

    if not state.active_account:
        error_msg('You must login first in order to register a cage')
        return
    
    list_cages(supress_header=True)
    cage_num = input('Enter Cage Number :')
    if not cage_num:
        error_msg('Cancelled')
        return
    cage_num = int(cage_num)
    cages = svc.find_cages_for_user(state.active_account)
    selected_cage = cages[cage_num - 1]

    success_msg(f'Selected Cage :{selected_cage.name}')
    start_date = parser.parse(input('Enter available date [yyyy-mm-dd] :'))
    days = int(input('No. of Days? :'))
    svc.add_available_date(selected_cage, start_date, days)
    state.reload_account()
    success_msg(f'Date added to cage: {selected_cage.name}')

def view_bookings():
    print(' ****************** Your bookings **************** ')

    if not state.active_account:
        error_msg("You must log in first to register a cage")
        return

    cages = svc.find_cages_for_user(state.active_account)

    bookings = [
        (c, b)
        for c in cages
        for b in c.bookings
        if b.booked_date is not None
    ]

    print("You have {} bookings.".format(len(bookings)))
    for c, b in bookings:
        print(' * Cage: {}, booked date: {}, from {} for {} days.'.format(
            c.name,
            datetime.date(b.booked_date.year,
                          b.booked_date.month, b.booked_date.day),
            datetime.date(b.check_in_date.year,
                          b.check_in_date.month, b.check_in_date.day),
            b.duration_in_days
        ))



def exit_app():
    print()
    print('bye')
    raise KeyboardInterrupt()


def get_action():
    text = '> '
    if state.active_account:
        text = f'{state.active_account.name}> '

    action = input(Fore.YELLOW + text + Fore.WHITE)
    return action.strip().lower()


def unknown_command():
    print("Sorry we didn't understand that command.")


def success_msg(text):
    print(Fore.LIGHTGREEN_EX + text + Fore.WHITE)


def error_msg(text):
    print(Fore.LIGHTRED_EX + text + Fore.WHITE)
