from pokerbots.engine.game import Raise, Check, Call, Bet, Fold, Post, Deal, Show, Card
from pokerbots.player.trickybot.hand_evaluator import HandEvaluator
from numpy import *

class trickybot:
    def __init__(self, param1=0.35, param2=0.95, param5=30, param6=20, param7=0.7, param8=1.0, param9=0.05):
        self.debug = False
        self.unlimited = False
        
        # my name
        self.name = "trickybot"

        # name of last opponent played
        self.opponent_name = None

        # game state variables -- these are updated by the engine which has its
        # own internal representation. so if you modify them, they'll just
        # be reset. we recommend leaving the remainder of the init as is
        self.hand = None # a tuple
        self.stack = None # hopefully an integer
        self.pip = None # integer, stake in pot
        self.button = None # boolean, true if you have the button
        self.opponent = None # dictionary with 'pip', 'button', 'name', 'stack' for opponent
        self.bb = None # size of current big blind
        self.sb = None # size of current small blind
        self.hands_played = None # number of hands played
        self.board = None # a Board object
        self.legal = None # list of allowed actions, e.g. [Raise(8), Call(), Fold()]
        self.actions = None
        self.last = None
        self.pot = None
        self.time = None
        
        # initial values of parameters
        self.param1 = param1
        self.param2 = param2
        self.param5 = param5
        self.param6 = param6
        self.param7 = param7
        self.param8 = param8
        self.param9 = param9
        
        self.reset_internal_values()

    def respond(self):
        """Based on your game state variables (see the __init__), make a
        decision and return an action. If you return an illegal action, the
        engine will automatically check/fold you
        """
        
        if self.hands_played != self.hand_counter:
            self.hand_counter = self.hands_played
            self.percentiles = {}
            self.slowplay_flag = False
        
        # see other templates for a modular way of determining an action
        if not self.board.board:
            if 'preflop' not in self.percentiles:
                self.percentiles['preflop'] = HandEvaluator.evaluate_hand(self.hand)
                self.played_this_street = 0
                if self.button:
                    self.opponent_previous_pip=2
                else:
                    self.opponent_previous_pip=1
            self.played_this_street += 1
            return self.strategy(2, self.percentiles['preflop'])
        elif self.board:
            if len(self.board.board) == 3:
                if 'flop' not in self.percentiles:
                    self.percentiles['flop'] = HandEvaluator.evaluate_hand(self.hand, self.board.cards)
                    self.played_this_street = 0
                    self.opponent_previous_pip=0
                self.played_this_street += 1
                return self.strategy(3, self.percentiles['flop'])
            elif len(self.board.board) == 4:
                if 'turn' not in self.percentiles:
                    self.percentiles['turn'] = HandEvaluator.evaluate_hand(self.hand, self.board.cards)
                    self.played_this_street = 0
                    self.opponent_previous_pip=0
                self.played_this_street += 1
                return self.strategy(4, self.percentiles['turn'])
            elif len(self.board.board) == 5:
                if 'river' not in self.percentiles:
                    self.percentiles['river'] = HandEvaluator.evaluate_hand(self.hand, self.board.cards)
                    self.played_this_street = 0
                    self.opponent_previous_pip=0
                self.played_this_street += 1
                return self.strategy(5, self.percentiles['river'])

        return Check()
    
    def strategy(self, street, percentile):
        """
        Returns an action before the flop, based on the table and the player
        """

        if random.rand(1) < self.p9 and self.stack > 2*self.pot:
            if self.pot == 2*self.bb:
                return Bet(3*self.pot)
            elif self.pot == self.bb+self.sb:
                return Raise(3*self.pot)
            
        if self.played_this_street > 1:
            self.slowplay_flag = True 
        
        if len(self.opponent_bet_history) > self.p5:
            self.opponent_bet_history = self.opponent_bet_history[-self.p5:]

        
        x = percentile            
        s = self.slow_play_threshold

        A = self.p1*(1-self.p7) + self.potodds_ratio_variable*self.p7

        #print self.opponent['pip'],self.opponent_previous_pip
        opponent_bet = 1.0*(self.opponent['pip'] - self.opponent_previous_pip)/self.pot
        self.opponent_previous_pip = self.opponent['pip']
        chips_to_add = self.opponent['pip'] - self.pip #size of opponent's bet 

        # predict opponents strength based on their bets
        if opponent_bet > 0:
            self.opponent_bet_history.append(opponent_bet)
            self.potodds_ratio_variable = ((1-1.0/self.p6)*self.potodds_ratio_variable + 2.0/self.p6*opponent_bet)
            y = 1.0*sum(opponent_bet > array(self.opponent_bet_history))/len(self.opponent_bet_history) + 0.5*sum(opponent_bet == array(self.opponent_bet_history))/len(self.opponent_bet_history)
            if x == 1 and y == 1:
                z == 1
            else:
                z = x*(1-y)/(x*(1-y)+(1-x)*y) * self.p8 + x * (1-self.p8)
            if len(self.opponent_bet_history) >= self.p5/2 and street > 2:
                mu = mean(self.opponent_bet_history)
                sigma = std(self.opponent_bet_history)
                if mu > 0 and sigma/mu > 0.1:
                    x = z
        
        if x <= s:
            alpha = A*x
        elif x <= 1.0:
            alpha = 0

        if alpha < 1:
            value_bet = int(round(alpha/(1-alpha)*self.pot))
        else:
            value_bet = self.stack

        if x <= s:
            alphacall = A*x
        elif x <= 1:
            alphacall = 1 #make sure we call anything in our slowplay zone
            
        if alphacall < 1:
            value_call = int(round(alphacall/(1-alphacall)*self.pot))
        else:
            value_call = self.stack
            
        #print alphacall,value_call

        if street == 5:
            value_bet = value_call
        
        for action in self.legal:
            
            if isinstance(action, Bet):
                       
                if not(self.button) and (street == 3 or street == 4): # first to act after flop,turn
                    self.played_this_street -= 1 #won't count this check as playing
                    return Check()

                if x > s and self.button: # Second to act (in position) with nuts
                    if self.slowplay_flag: #if they have good cards, lets push them
                        return Bet(self.pot)
                    else:
                        value_bet = int(floor(.75*self.pot*random.rand(1)))+int(round(.25*self.pot))
                        
                if self.slowplay_flag:
                    return Check()
                
                if value_bet >= self.stack:
                    return Bet(self.stack)
                elif value_bet > 0:
                    return Bet(value_bet)
                else:
                    return Check()

            elif isinstance(action, Raise):
                
                if x > s: # pump money out with reraising (always min raise)
                    random_addition = int(floor(3*random.rand(1)))
                    #random between 0 and 2 to throw off pattern-recognizers for string bets
                    if 2*chips_to_add + random_addition <= self.stack:
                        return Raise(self.pip+2*chips_to_add + random_addition)
                    else:
                        return Raise(self.stack + self.pip)
                
                else:
                    if value_bet >= self.stack:
                        if value_bet <= chips_to_add or self.slowplay_flag: #defense
                            return Call()
                        else:
                            return Raise(self.stack + self.pip)
                    elif value_bet >= 2 * chips_to_add:
                        if self.slowplay_flag: #defense against bleeding
                            return Call()
                        else:
                            return Raise(value_bet + self.pip)
                    elif value_call >= chips_to_add:
                        return Call()
                    else:
                        return Fold()
            
            elif isinstance(action, Call): #only options are calling and folding
                
                if value_call >= chips_to_add:
                    return Call()
                else:
                    return Fold()

                
        # if something screws up, try checking
        return Check()
    
    
    def reset_internal_values(self):
    
        # to keep hand_history
        self.hand_counter = 0
        # to store percentiles for this hand
        self.percentiles = {}
        self.opponent_percentiles = {}
        
        self.p1 = self.param1
        self.potodds_ratio_variable = self.param1
        # self.p1 is used for determining the fixed portion of A

        self.p2 = self.param2
        self.slow_play_threshold = self.param2
        # minimum hand percentile before we reduce our bet strength (slow play)

        self.p5 = self.param5
        # number of bets required to use psychic betting analysis of opponent
        
        self.p6 = self.param6
        # number of bets to use in finding the variable component of A
        
        self.p7 = self.param7
        # variable component of A
        
        self.p8 = self.param8
        # fraction of EV calculated via psychic powers

        self.p9 = self.param9
        # percent of time we stab at pot preflop
        
        self.opponent_bet_history = []
        self.opponent_previous_pip = 0

        self.played_this_street = 0
        #number of times we have acted this street, including current action

        self.slowplay_flag = False

  
    def reset(self, won, last_hand):
        """Reset accepts a boolean indicating whether you won a match and
        provides the last hand if you want to update any statistics from it
        """
        
        self.reset_internal_values()
