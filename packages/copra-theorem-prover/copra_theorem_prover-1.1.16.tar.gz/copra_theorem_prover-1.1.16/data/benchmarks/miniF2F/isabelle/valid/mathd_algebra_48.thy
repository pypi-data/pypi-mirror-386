(*
  Authors: Albert Qiaochu Jiang
*)

theory mathd_algebra_48 imports
  Complex_Main
begin

theorem mathd_algebra_48:
  fixes q e :: complex
  assumes h0 : "q = Complex 9 (-4)"
    and h1 : "e = Complex (-3) (-4)"
  shows "q - e = 12"
  unfolding h0 h1
  by eval

end