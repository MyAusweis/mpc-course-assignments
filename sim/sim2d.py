import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from scipy.optimize import minimize
import time


def sim_run(options, MPC):
    start = time.clock()
    # Simulator Options
    FIG_SIZE = options['FIG_SIZE'] # [Width, Height]

    mpc = MPC()

    prediction_horizon = 20
    num_inputs = 2
    u = np.zeros(prediction_horizon*num_inputs)
    bounds = []

    ref_1 = [10,10,0]
    ref_2 = [10, 2, 3.14159/2]
    ref = ref_1

    for i in range(prediction_horizon):
        bounds += [[-5, 5]]
        bounds += [[-0.8, 0.8]]

    state_i = np.array([[0,0,0,0]])
    u_i = np.array([[0,0]])
    sim_total = 250
    predict_info = [state_i]

    for i in range(1,sim_total+1):
        u = np.delete(u,0)
        u = np.delete(u,0)
        u = np.append(u, u[-2])
        u = np.append(u, u[-2])
        start_time = time.time()
        u_solution = minimize(mpc.cost_function, u, (prediction_horizon, state_i[-1], ref),
                                method='SLSQP',
                                bounds=bounds,
                                tol = 1e-5)
        print('Step ' + str(i) + ' of ' + str(sim_total) + '   Time ' + str(round(time.time() - start_time,5)))
        u = u_solution.x
        y = mpc.plant_model(state_i[-1], 0.1, u[0], u[1])
        if (i > 130):
            ref = ref_2
        predicted_state = np.array([y])
        for j in range(1,prediction_horizon):
            predicted = mpc.plant_model(predicted_state[-1], 0.1, u[2*j], u[2*j+1])
            predicted_state = np.append(predicted_state, np.array([predicted]), axis=0)
        predict_info += [predicted_state]
        state_i = np.append(state_i, np.array([y]), axis=0)
        #print(u_i)
        #print(np.array((u[0], u[1])))
        u_i = np.append(u_i, np.array([(u[0], u[1])]), axis=0)

    ###################
    # SIMULATOR DISPLAY

    # Total Figure
    fig = plt.figure(figsize=(FIG_SIZE[0], FIG_SIZE[1]))
    gs = gridspec.GridSpec(8,8)

    # Elevator plot settings.
    ax = fig.add_subplot(gs[:8, :8])

    plt.xlim(-2, 15)
    ax.set_ylim([-3, 15])
    #plt.xticks([])
    plt.title('MPC 2D')

    # Time display.
    time_text = ax.text(6, 0.5, '', fontsize=15)

    # Main plot info.
    car_width = 1.0
    patch_car = mpatches.Rectangle((0, 0), car_width, 2.5, fc='k', fill=False)
    patch_goal = mpatches.Rectangle((0, 0), car_width, 2.5, fc='b',
                                    ls='dashdot', fill=False)

    ax.add_patch(patch_car)
    ax.add_patch(patch_goal)
    predict, = ax.plot([], [], 'r--', linewidth = 1)

    # Car steering and throttle position.
    telem = [5,10]
    patch_wheel = mpatches.Circle((telem[0]-3, telem[1]), 2.2)
    ax.add_patch(patch_wheel)
    wheel_1, = ax.plot([], [], 'k', linewidth = 3)
    wheel_2, = ax.plot([], [], 'k', linewidth = 3)
    wheel_3, = ax.plot([], [], 'k', linewidth = 3)
    throttle_outline, = ax.plot([telem[0], telem[0]], [telem[1]-2, telem[1]+2],
                                'b', linewidth = 20, alpha = 0.4)
    throttle, = ax.plot([], [], 'k', linewidth = 20)
    brake_outline, = ax.plot([telem[0]+3, telem[0]+3], [telem[1]-2, telem[1]+2],
                            'b', linewidth = 20, alpha = 0.2)
    brake, = ax.plot([], [], 'k', linewidth = 20)
    throttle_text = ax.text(telem[0], telem[1]-3, 'Forward', fontsize = 15,
                        horizontalalignment='center')
    brake_text = ax.text(telem[0]+3, telem[1]-3, 'Reverse', fontsize = 15,
                        horizontalalignment='center')
    # V Estimate plot.
    # ax2 = fig.add_subplot(gs[0:4, 4:])
    # v_est, = ax2.plot([], [], '-b')
    # plt.title('V Estimate')
    # plt.xticks([])
    # ax2.set_ylim([0,4])
    # ax2.set_yticks([0,2,4])
    #
    # # X Estimate plot.
    # ax3 = fig.add_subplot(gs[5:9, 4:])
    # x_est, = ax3.plot([], [], '-b')
    # plt.title('X Estimate Error')
    # plt.xticks([])
    # ax3.set_ylim(-4,4)
    # ax3.set_yticks([-4,0,4])

    # Shift xy, centered on rear of car to rear left corner of car.
    def car_patch_pos(x, y, psi):
        #return [x,y]
        x_new = x - np.sin(psi)*(car_width/2)
        y_new = y + np.cos(psi)*(car_width/2)
        return [x_new, y_new]

    def steering_wheel(wheel_angle):
        wheel_1.set_data([telem[0]-3, telem[0]-3+np.cos(wheel_angle)*2],
                         [telem[1], telem[1]+np.sin(wheel_angle)*2])
        wheel_2.set_data([telem[0]-3, telem[0]-3-np.cos(wheel_angle)*2],
                         [telem[1], telem[1]-np.sin(wheel_angle)*2])
        wheel_3.set_data([telem[0]-3, telem[0]-3+np.sin(wheel_angle)*2],
                         [telem[1], telem[1]-np.cos(wheel_angle)*2])

    def update_plot(num):
        # Car.
        patch_car.set_xy(car_patch_pos(state_i[num,0], state_i[num,1], state_i[num,2]))
        patch_car._angle = np.rad2deg(state_i[num,2])-90
        # Car wheels
        steering_wheel(u_i[num,1]*2)
        throttle.set_data([telem[0],telem[0]],
                        [telem[1]-2, telem[1]-2+max(0,u_i[num,0]/5*4)])
        brake.set_data([telem[0]+3, telem[0]+3],
                        [telem[1]-2, telem[1]-2+max(0,-u_i[num,0]/5*4)])

        # Goal.
        if (num <= 130):
            patch_goal.set_xy(car_patch_pos(ref_1[0],ref_1[1],ref_1[2]))
            patch_goal._angle = np.rad2deg(ref_1[2])-90
        else:
            patch_goal.set_xy(car_patch_pos(ref_2[0],ref_2[1],ref_2[2]))
            patch_goal._angle = np.rad2deg(ref_2[2])-90

        #print(str(state_i[num,3]))
        predict.set_data(predict_info[num][:,0],predict_info[num][:,1])
        # Timer.
        #time_text.set_text(str(100-t[num]))

        return patch_car, time_text


    print("Compute Time: ", round(time.clock() - start, 3), "seconds.")
    # Animation.
    car_ani = animation.FuncAnimation(fig, update_plot, frames=range(1,len(state_i)), interval=100, repeat=True, blit=False)
    #car_ani.save('lines.mp4')

    plt.show()
