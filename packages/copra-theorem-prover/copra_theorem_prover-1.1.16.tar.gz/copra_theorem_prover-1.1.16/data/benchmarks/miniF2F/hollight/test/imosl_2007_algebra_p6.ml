let imosl-2007-algebra-p6 = `!a:num->real.
    (!k. a k >= &0) /\
    sum (0..(100-1)) (\x. (a (x + 1)) pow 2) = &1
==>
    sum (0..(99-1)) (\x. ((a (x + 1)) pow 2 * a (x + 2))) + (a 100) pow 2 * a 1 < &12 / &25
`;;
