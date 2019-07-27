from datetime import datetime, timedelta
import numbers


class Result(object):
	def __init__(self, name, description, remaining=0, units="days"):
		self.name = name
		self.description = description
		self.remaining = remaining
		self.units = units

	@property
	def remaining(self):
		return self.__remaining

	@remaining.setter
	def remaining(self, remaining):
		if isinstance(remaining, numbers.Number):
			self.__remaining = remaining
		else:
			self.__remaining = remaining
			raise Exception('progress must be a number')

# All top indicators should reach 100% at their conservative estimate
# We want to predict when we're very close to the top, 
# not observe when it happened after the fact

# This is more a collection of codified thoughts than anything else.

# For the most part I don't think data pre-2012 is very relevant or reliable
# Data from 2013 onward is preferable, 2014+ is ideal

# def day_countdown(end):
# 	time_left = end.days / (end - start).days

# 	return time_left
	

def days_after_halvening():
	result = Result("Halvening", "Price has historically reached a peak 400-500 days after halvening events")

	halvening = datetime(2020, 5, 19) # Predicted halvening May 19 2020
	end = halvening + timedelta(days=400) # 400-500 days after halvening

	result.remaining = (end - datetime.now()).days

	return result


def full_cycle_length():
	result = Result("Full Top to Top Cycle", "Cycle lengths appear to be getting longer, based on previous cycle of ~4 years")
	# There's some evidence/belief that cycles are lengthening

	start = datetime(2017, 12, 17) # Top of last cycle
	end = start + timedelta(days=1477)

	result.remaining = (end - datetime.now()).days

	return result


if __name__ == "__main__":
	indicators = [days_after_halvening(), full_cycle_length()]

	for indicator in indicators:
		print(f'{indicator.name}: {indicator.remaining} {indicator.units} remaining')


