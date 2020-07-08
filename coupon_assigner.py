import pandas as pd

########################
## Problem Parameters ##
########################

n_coups = len(10) #how many coupons per user
n_users = 200000
budget = 5000

# Data is put in the format (coup_num_i, value_i, cost_i)
data = [[(j,value_columns[i,j],cost_columns[i,j]) for j in range(0,n_coups)] for i in range(n_users)]

#####################
### Preprocessing ###
#####################

# Order functions - to order by ascending values, weights, ratios and finally by break points.
def ordering_fn(T,k=0,reverse=True):
    T.sort(key=lambda e: e[k],reverse=True)

def value_equality_filter():
    # corrects against vi=0 and vi = vi+1
    i=0
    while i<=len(L)-1:
        condition1 = (L[i][1] == 0)
        if condition1:
            del L[i]
            continue
        if i==len(L)-1: break  # 1 element left no pairs can be found  
        condition2 = (L[i][1] == L[i + 1][1]) 
        if condition2:
            i_ = i + np.argmax([L[i][2], L[i + 1][2]])
            del L[i_]
            continue
        i+=1

def cost_ratio_filter():
    # Eliminate coupons not following 0< v1 < v2 < ..., 0 < w1 < w2 < ... or w1/v1 < w2/v2 < ...
    j=0
    while j<=len(L)-1:
        condition1 = (L[j][2]==0) 
        if condition1:
            del L[j]
            continue    
        if j==len(L)-1: break
        condition2 = (L[j][2]<=L[j+1][2]) 
        condition3 = (L[j][2]/L[j][1]<=L[j+1][2]/L[j+1][1])
        if condition2 or condition3:
            del L[j+1]
            continue
        j+=1

def break_point_filter():
    # Eliminate coupons according to breakpoints as λ1 > λ2 > ...
    # Rule to eliminate j: j>i but λj >= λi
    i = -2
    bps = [L[-1][1]/L[-1][2]] #initialize break points with vgi/cgi
    while len(L) + i >= 0:
        ratio = (L[i][1] - L[i+1][1])/((L[i][2] - L[i+1][2]))
        if ratio >= bps[0]:
            if i==-2: #make sure we don't delete λ1
              del L[-2]
              continue
            else:
              del L[i+1]
              del bps[0]
              i+=1
            continue
        bps = [ratio] + bps
        i-=1
    return bps

# Perform the filter/sort
breakpoints = []
for L in data: # 1 loop for all users
    ordering_fn(L,1)
    value_equality_filter()
    cost_ratio_filter()
    breakpoints.append(break_point_filter())
    
##############
### Solver ###
##############

# initialize the queue and cost
N = len(data)
S = budget
key = lambda e : e[1] # order by break point size
# each queue element looks like: 
#(user num, breakpoint, coupon num, value, cost)
queue = [(i,breakpoints[i][j],*d) for i in range(N) for j,d in enumerate(data[i])] 
queue.sort(key=key,reverse=True)
cost_coup_assignments = np.zeros((n_users,3)) #storage for viable cost, value and coupon number
cost_coup_assignments[:,2] = -1

# progress bar
loop_lim = n_coups * n_users
counter = 0
update_count = 10000

while len(queue)>0:
    # keep track of progress
    counter += 1
    if counter%update_count==0:
      print('Progress ',counter,'/',loop_lim,'(max.)')
    # pop queue and update solution
    q = queue.pop(0)
    user = q[0]
    value = q[3]
    coup_num = q[2]
    cost_old = cost_coup_assignments[user,0]
    cost_new = q[4]
    diff = S + (cost_old - cost_new)
    if diff < 0:
        break
    S = diff
    cost_coup_assignments[user,0] = cost_new
    cost_coup_assignments[user,1] = value
    cost_coup_assignments[user,2] = coup_num
    
df_results = pd.DataFrame(cost_coup_assignments,columns=['Cost','Value','Coupon_no'])
