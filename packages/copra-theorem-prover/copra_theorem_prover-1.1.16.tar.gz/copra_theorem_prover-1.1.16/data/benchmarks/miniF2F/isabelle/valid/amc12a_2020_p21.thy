(*
  Authors: Wenda Li
*)

theory amc12a_2020_p21 
  imports Complex_Main "HOL-Computational_Algebra.Computational_Algebra"
    "HOL-Number_Theory.Number_Theory"
begin

theorem amc12a_2020_p21:
  "card {n :: nat. 5 dvd n \<and> lcm (fact 5) n 
          = 5 * gcd (fact 10) n} = 48"
  sorry

end