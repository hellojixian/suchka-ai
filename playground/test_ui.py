import time
from tqdm import tqdm

# Set the total number of iterations for each progress bar
total_iterations = 100

# Create and position the first progress bar
progress_bar_1 = tqdm(total=total_iterations, position=0, desc="Progress 1")

# Create and position the second progress bar
progress_bar_2 = tqdm(total=total_iterations, position=1, desc="Progress 2")

# Create and position the third progress bar
progress_bar_3 = tqdm(total=total_iterations, position=2, desc="Progress 3")

# Create and position the fourth progress bar
progress_bar_4 = tqdm(total=total_iterations, position=3, desc="Progress 4")

# Update the progress bars
for i in range(total_iterations):
    progress_bar_1.update(1)
    progress_bar_2.update(1)
    progress_bar_3.update(1)
    progress_bar_4.update(1)
    time.sleep(0.01)

progress_bar_3.desc = 'new task'
progress_bar_3.reset(total=total_iterations*2)
for i in range(total_iterations):
  progress_bar_3.update(1)
  time.sleep(0.1)
# Close the progress bars
progress_bar_1.close()
progress_bar_2.close()
progress_bar_3.close()
progress_bar_4.close()