from modules.rank_modes import service

service.configure({})

player_1900_20={"rank_points":1900,"wins":10,"draws":3,"losses":7,"total_matches":0}
expected={
 "rank_random":True,
 "random3_pick1":True,
 "tactical_bo3":True,
 "bo3":True,
 "ban_pick_bo3":True,
 "home_away":True,
}
for code,wanted in expected.items():
 result=service.check_rank_mode_eligibility(code,player_1900_20)
 assert result["eligible"] is wanted,(code,result)

player_1900_10={"rank_points":1900,"wins":5,"draws":2,"losses":3}
assert service.check_rank_mode_eligibility("home_away",player_1900_10)["eligible"]
assert not service.check_rank_mode_eligibility("bo3",player_1900_10)["eligible"]
assert "15 trận" in " ".join(service.check_rank_mode_eligibility("bo3",player_1900_10)["reasons"])

player_1400_20={"rank_points":1400,"wins":12,"draws":2,"losses":6}
assert service.check_rank_mode_eligibility("bo3",player_1400_20)["eligible"]
assert not service.check_rank_mode_eligibility("tactical_bo3",player_1400_20)["eligible"]
print("PASS: rank mode unlock V1.3.3")
