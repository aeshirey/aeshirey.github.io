---
layout: post
title:  "Energy efficiency research: heat pump dryers"
date:   2021-04-13 23:12:36 -0700
category: code
tags: [energy-efficiency]
---

_See this video: [The Future of Heat Pumps is Underground (and other places, too!)](https://www.youtube.com/watch?v=7zrx-b2sLUs)_

As [I really want](https://twitter.com/adamshirey/status/1377694632671256577) a concise, data-driven economical and environmental summary of different energy efficiency projects I can consider, I decided I would do some analysis and go ahead and start writing my analyses. Below are my notes on researching less inefficient clothes dryers. More to come!

# Preface
I don't have any of these appliances, and this is a preliminary bit of research. Our dryer is in our garage, so the air temperature there is generally somewhere between outside ambient and about 68° (inside) temperature. We're currently using a conventional, vented electric dryer and paying around $0.10/kWh for much of our electricity.

I'm using dollar amounts as a way to decide whether to pick something and which option to pick and as a proxy for environmental impact.

From an _economic_ perspective, if I treat a purchase of some energy efficienc appliance as an investment, I'll compare it against a 9% annual return. The appliance will cost some amount, $X, and when lower energy costs save me $X over some period of time, I now have 'doubled' my investment: I have saved the original purchase price _and_ I have the appliance itself to continue saving more money. I'm grossly simplifying by assuming the appliance will last forever. A 9% interest rate will double in `$X*2 = $X*1.09^t` or `2 = 1.09^t` or `log(2)/log(1.09)` = 8 years, so purely on the economics, anything that can pay for itself in less than 8 years is probably a good bet, and the shorter the return period, the better.

# Heat Pump Clothes Dryer

### Pros
* Ventless
* Some can be 110v, so can be placed anywhere
* Because it uses lower temperatures, it is gentler on clothes.

### Cons
* Can be 3-4x as expensive (to buy) vs a conventional vented dryer
* Loads can take 1.5hrs to dry instead of 45m
* Removed moisture has to be drained/dumped

### Cost analysis
Electric dryer baseline:
* Assume electric dryer uses 4 kWh/load<sup>[\[1\]](https://www.directenergy.com/learning-center/how-much-energy-dryer-use)</sup> @ $0.10/kWh = $0.40/load
* Assume 7 cu ft capacity that directly correlates with load size
* Assume 4 kWh/load @ $0.10/kWh = $0.40/load
* Assume 5 loads/wk * 52 weeks * $0.40/load = $104/year

Heat pump comparison:
* Assume a marginal purchase cost of $1000 for the heat pump dryer
* Assume 1 kWh/load<sup>[\[2\]](https://en.wikipedia.org/wiki/Clothes_dryer#Heat_pump_dryers)</sup> * $0.10/kWh = $0.10/load
* Assume 5 loads/wk * 52wks/yr * $0.10/load = $26/yr 
* ROI is: marginal purchase cost $1000 divided by ($104-26) = $78/yr savings is **12.8 years**
* There might be EnergyStar rebates to reduce the purchase price
* In the winter, since no conditioned air is vented outside, there may be extra savings thanks to keeping the garage a closed system

[Example dryer](https://www.lowes.com/pd/Whirlpool-7-4-cu-ft-Stackable-Ventless-Electric-Dryer-Chrome-Shadow-ENERGY-STAR/1000716664)

# Condenser Clothes Dryer
There are also condenser dryers that are cheaper up-front but twice as energy intense as heat pump dryers. They seem to be a good middle-ground between conventional vented and heat pumps, though they are also often smaller in size (~4 cu ft versus conventional and heat pump 7 cu ft).

### Cost analysis
* Assume the marginal purchase cost is $500
* Assume load size is (4/7) and thus we're doing (7/4) as many loads
* Assume 2 kWh/load<sup>[\[3\]](https://en.wikipedia.org/wiki/Clothes_dryer#Condenser_dryers)</sup> * $0.10/kWh = $0.20/load
* (5*7/4) loads/wk * 52wks/yr * $0.20/load = $91/yr
* ROI is: marginal purchase cost $500 divided by ($104-91) = $78/yr savings is **38.5 years**
* Rebates and extra savings points from heat pump dryer also apply here.

[Example dryer](https://www.lowes.com/pd/GE-4-1-cu-ft-Stackable-Ventless-Electric-Dryer-White/1000731570)

# Spin Dryer intermediate step?
Using a spin dryer, [this site](https://www.greenandgrowing.org/money-energy-laundry-spin-dryer/) claims that a five minute cycle at 400W can reduce the drying cycle time by half. 

### Pros
* 400W would be low enough to run on a 110V outlet, so it could be placed anywhere
* Reduced drying times
* In some situations, could dry clothes 'well enough' and obviate the need for the other dryer

### Cons
* Extra step involved
* Extra appliance needed

### Cost analysis
* Assuming that's correct, a first pass might cost 0.4 kW * (5/60) hr = $0.033/load to spin.
* This is also 5 loads/wk * 52wks/yr * 0.033/load = $8.67/yr.
* Assuming a purchase price of around $160 (for example, with [this product](https://www.amazon.com/Laundry-Alternative-Centrifugal-High-Tech-Suspension/dp/B07X3MWR3V))
* Assuming heat pump is used for the second step, annual cost is halved to $13, so combined annual cost is $21.66.
    * The ROI is now ($1000 heat pump + $160 spin dryer) divided by ($104-21.66)/yr = **14.1 years**
* Assuming condenser dryer is used for the second step, annual cost is halved to $45.50, so combined annual cost is $54.17
    * The ROI is now ($500 heat pump + $160 spin dryer) divided by ($104-54.17)/yr = **13.2 years**
* Assuming only a spin dryer is used with a conventional dryer, the annual cost is dropped from $104 to $52.
    * The ROI is now $160 spin dryer divided by 52 = **3.1 years**

# Opinion
In summary, a spin dryer has a really attractive ROI if you're willing to put up with having the extra appliance occupying space and the extra step involved.

For environmental purposes, a heat pump dryer seems much better than a condenser dryer. The additional drying time might be a problem, though this could be mitigated by first spinning.
