extends Node

var failures: int = 0
var next_uid: int = 10000

func _ready() -> void:
	_test_distribution_and_unique_instances()
	_test_groups_and_duplicate_suits()
	_test_runs_and_ace_rules()
	_test_multiple_jokers()
	_test_turn_state_machine()
	_test_scoring()
	_test_final_discard_wins()
	_test_opening_rule_is_configurable()
	if failures == 0:
		print("RAMI_TESTS: PASS")
		get_tree().quit(0)
	else:
		push_error("RAMI_TESTS: FAIL count=%d" % failures)
		get_tree().quit(1)

func _expect(condition: bool, message: String) -> void:
	if condition:
		print("TEST_OK: ", message)
	else:
		failures += 1
		push_error("TEST_FAIL: %s" % message)

func _card(suit: String, rank: String, deck_index: int = 0) -> CardInstance:
	var card: CardInstance = CardInstance.new(next_uid, deck_index, suit, rank, "")
	next_uid += 1
	return card

func _joker(color: String = "black", deck_index: int = 0) -> CardInstance:
	var card: CardInstance = CardInstance.new(next_uid, deck_index, "", "", color)
	next_uid += 1
	return card

func _cards(values: Array) -> Array[CardInstance]:
	var out: Array[CardInstance] = []
	for value: Variant in values:
		if value is CardInstance:
			out.append(value as CardInstance)
	return out

func _test_distribution_and_unique_instances() -> void:
	var game: RamiGame = RamiGame.new()
	game.new_round()
	_expect(game.player_hand.size() == 13, "13 cartes pour le joueur")
	_expect(game.ai1_hand.size() == 13, "13 cartes pour IA1")
	_expect(game.ai2_hand.size() == 13, "13 cartes pour IA2")
	_expect(game.stock.size() == 68, "68 cartes dans la pioche après distribution")
	_expect(game.discard_pile.size() == 1, "1 carte initiale dans la défausse")
	_expect(game.phase == RamiGame.Phase.DRAW, "la manche commence en phase PIOCHE")

	var all_cards: Array[CardInstance] = []
	for card: CardInstance in game.player_hand:
		all_cards.append(card)
	for card: CardInstance in game.ai1_hand:
		all_cards.append(card)
	for card: CardInstance in game.ai2_hand:
		all_cards.append(card)
	for card: CardInstance in game.stock:
		all_cards.append(card)
	for card: CardInstance in game.discard_pile:
		all_cards.append(card)
	_expect(all_cards.size() == 108, "108 instances physiques/logiques au total")
	var seen: Dictionary = {}
	for card: CardInstance in all_cards:
		seen[card.uid] = true
	_expect(seen.size() == 108, "chaque CardInstance possède un UID unique")

func _test_groups_and_duplicate_suits() -> void:
	var game: RamiGame = RamiGame.new()
	var valid_group: Array[CardInstance] = _cards([_card("hearts", "7"), _card("diamonds", "7"), _card("spades", "7")])
	_expect(bool(game.validate_meld(valid_group).get("valid", false)), "7♥ 7♦ 7♠ est un groupe valide")
	var invalid_duplicate: Array[CardInstance] = _cards([_card("hearts", "7", 0), _card("hearts", "7", 1), _card("diamonds", "7")])
	_expect(not bool(game.validate_meld(invalid_duplicate).get("valid", false)), "deux 7♥ dans le même groupe sont interdits")
	var four_group: Array[CardInstance] = _cards([_card("hearts", "9"), _card("diamonds", "9"), _card("spades", "9"), _card("clubs", "9")])
	_expect(bool(game.validate_meld(four_group).get("valid", false)), "un carré de quatre couleurs est valide")

func _test_runs_and_ace_rules() -> void:
	var game: RamiGame = RamiGame.new()
	_expect(bool(game.validate_meld(_cards([_card("hearts", "A"), _card("hearts", "2"), _card("hearts", "3")])).get("valid", false)), "A-2-3 est autorisé")
	_expect(bool(game.validate_meld(_cards([_card("clubs", "Q"), _card("clubs", "K"), _card("clubs", "A")])).get("valid", false)), "Q-K-A est autorisé")
	_expect(not bool(game.validate_meld(_cards([_card("spades", "K"), _card("spades", "A"), _card("spades", "2")])).get("valid", false)), "K-A-2 est interdit")
	_expect(bool(game.validate_meld(_cards([_card("diamonds", "4"), _card("diamonds", "5"), _card("diamonds", "6"), _card("diamonds", "7"), _card("diamonds", "8")])).get("valid", false)), "une suite peut contenir 5 cartes ou plus")

func _test_multiple_jokers() -> void:
	var game: RamiGame = RamiGame.new()
	var run_with_two_jokers: Array[CardInstance] = _cards([_card("hearts", "5"), _joker("black"), _joker("red"), _card("hearts", "8")])
	_expect(bool(game.validate_meld(run_with_two_jokers).get("valid", false)), "plusieurs Jokers sont autorisés dans une suite logique")
	var set_with_two_jokers: Array[CardInstance] = _cards([_card("clubs", "10"), _joker("black"), _joker("red")])
	_expect(bool(game.validate_meld(set_with_two_jokers).get("valid", false)), "plusieurs Jokers sont autorisés dans un groupe")

func _test_turn_state_machine() -> void:
	var game: RamiGame = RamiGame.new()
	game.new_round()
	var before: int = game.player_hand.size()
	var premature_discard: Dictionary = game.discard_player(0)
	_expect(not bool(premature_discard.get("ok", false)), "impossible de défausser avant d'avoir pioché")
	_expect(game.draw_stock(), "la pioche est possible au début du tour")
	_expect(game.phase == RamiGame.Phase.ACTION, "piocher fait passer en phase ACTION")
	_expect(game.player_hand.size() == before + 1, "la pioche ajoute exactement une carte")
	_expect(not game.draw_stock(), "impossible de piocher deux fois dans le même tour")

func _test_scoring() -> void:
	var game: RamiGame = RamiGame.new()
	var hand: Array[CardInstance] = _cards([_card("spades", "A"), _card("hearts", "K"), _card("clubs", "7"), _joker("red")])
	_expect(game.hand_score(hand) == 48, "score = As 11 + Roi 10 + 7 + Joker 20")

func _test_final_discard_wins() -> void:
	var game: RamiGame = RamiGame.new()
	game.new_round()
	game.player_hand.clear()
	game.player_hand.append(_card("diamonds", "3"))
	game.turn_index = 0
	game.phase = RamiGame.Phase.ACTION
	var result: Dictionary = game.discard_player(0)
	_expect(bool(result.get("ok", false)), "la dernière carte peut être défaussée")
	_expect(game.winner_index == 0, "défausser la dernière carte gagne immédiatement")
	_expect(game.hand_score(game.player_hand) == 0, "le gagnant termine à 0 point")

func _test_opening_rule_is_configurable() -> void:
	var game: RamiGame = RamiGame.new()
	_expect(game.opening_rule == RamiGame.OpeningRule.SIMPLE_MELD, "l'ouverture simple est la règle active par défaut")
	game.set_opening_rule(RamiGame.OpeningRule.RAMI_51)
	_expect(game.opening_rule_name() == "Rami 51", "le moteur peut basculer vers la règle Rami 51")
	game.player_hand.clear()
	game.player_hand.append_array(_cards([
		_card("hearts", "10"), _card("hearts", "J"), _card("hearts", "Q"), _card("hearts", "K"), _card("hearts", "A"), _card("clubs", "2")
	]))
	game.turn_index = 0
	game.phase = RamiGame.Phase.ACTION
	var selection: Array[int] = [0, 1, 2, 3, 4]
	var result: Dictionary = game.play_player_selection(selection)
	_expect(bool(result.get("ok", false)), "une ouverture 10-J-Q-K-A à 51 points avec tierce franche passe en mode Rami 51")
