# Created By: Virgil Dupras
# Created On: 2009-06-03
# Copyright 2013 Hardcoded Software (http://www.hardcoded.net)
# 
# This software is licensed under the "BSD" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/bsd_license

# ABOUT BUDGETS
# Budgets work very similarly to recurrences, except that a twist must be applied to them so they
# can work properly. The twist is about the spawn's "recurrence" date and the effective date. The
# recurrence date must be at the beginning of the period, but the effective date must be at the end
# of it. The reason for it is that since recurrence are only cooked until a certain date (usually
# the current date range's end), but that the budget is affects the date range *prior* to it, the
# last budget of the date range will never be represented.

from datetime import date

from hscommon.util import extract

from .amount import prorate_amount
from .date import DateRange, ONE_DAY
from .recurrence import Recurrence, Spawn, DateCounter, RepeatType
from .transaction import Transaction, Split

class BudgetSpawn(Spawn):
    is_budget = True

class Budget(Recurrence):
    def __init__(self, account, target, amount, ref_date, repeat_type=RepeatType.Monthly):
        self.account = account
        self.target = target
        self.amount = amount
        self.notes = ''
        self._previous_spawns = []
        ref = Transaction(ref_date)
        Recurrence.__init__(self, ref, repeat_type, 1)
    
    def __repr__(self):
        return '<Budget %r %r %r>' % (self.account, self.target, self.amount)
    
    #--- Override
    def _create_spawn(self, ref, recurrence_date):
        # `recurrence_date` is the date at which the budget *starts*.
        # We need a date counter to see which date is next (so we can know when our period ends
        date_counter = DateCounter(recurrence_date, self.repeat_type, self.repeat_every, date.max)
        next(date_counter) # first next() is the start_date
        end_date = next(date_counter) - ONE_DAY
        return BudgetSpawn(self, ref, recurrence_date=recurrence_date, date=end_date)
    
    def get_spawns(self, end, transactions, consumedtxns):
        # transactions will affect the amounts of the budget spawns
        # consumedtxns is a set of txns already "consumed" by a budget. It is the budget's
        # responsability to add txns to this set as it "consumes" them
        spawns = Recurrence.get_spawns(self, end)
        # No spawn in the past
        spawns = [spawn for spawn in spawns if spawn.date > date.today()]
        account = self.account
        budget_amount = self.amount if account.is_debit_account() else -self.amount
        relevant_transactions = set(t for t in transactions if account in t.affected_accounts())
        relevant_transactions -= consumedtxns
        for spawn in spawns:
            affects_spawn = lambda t: spawn.recurrence_date <= t.date <= spawn.date
            wheat, shaft = extract(affects_spawn, relevant_transactions)
            relevant_transactions = shaft
            txns_amount = sum(t.amount_for_account(account, budget_amount.currency) for t in wheat)
            if abs(txns_amount) < abs(budget_amount):
                spawn_amount = budget_amount - txns_amount
                if spawn.amount_for_account(account, budget_amount.currency) != spawn_amount:
                    spawn.amount = abs(spawn_amount)
                    spawn.set_splits([Split(spawn, account, spawn_amount), Split(spawn, self.target, -spawn_amount)])
            else:
                spawn.set_splits([])
            consumedtxns |= set(wheat)
        self._previous_spawns = spawns
        return spawns
    
    #--- Public
    def amount_for_date_range(self, date_range, currency):
        total_amount = 0
        for spawn in self._previous_spawns:
            amount = spawn.amount_for_account(self.account, currency)
            if not amount:
                continue
            my_start_date = max(spawn.recurrence_date, date.today() + ONE_DAY)
            my_end_date = spawn.date
            my_date_range = DateRange(my_start_date, my_end_date)
            total_amount += prorate_amount(amount, my_date_range, date_range)
        return total_amount
    

class BudgetList(list):
    def amount_for_account(self, account, date_range, currency=None):
        if not date_range.future:
            return 0
        budgets = [b for b in self if b.account is account and b.amount]
        if not budgets:
            return 0
        currency = currency or account.currency
        amount = sum(b.amount_for_date_range(date_range, currency) for b in budgets)
        return amount
    
    def budgets_for_target(self, target):
        return [b for b in self if b.target is target]
    
    def normal_amount_for_account(self, account, date_range, currency=None):
        budgeted_amount = self.amount_for_account(account, date_range, currency)
        return account.normalize_amount(budgeted_amount)
    
