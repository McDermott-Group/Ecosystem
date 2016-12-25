function [R, Tcalib, T_IPTS68, T_ITS90] = pt1000

% Calibration extracted by explicitly plugging in the numbers into
% LabVIEW GUI and the using the PT1000 calibration option.
R = [15, 20, 35, 50:50:1150]; % Ohm
Tcalib = [1.2833 19.807 29.531 36.781 51.799 64.377 76.617 88.524 100.25...
          111.95 123.73 135.66 147.73 159.95 172.29 184.73 197.25 209.82...
          222.43 235.07 247.74 260.44 273.16 285.91 298.72 311.58]; % K

% PT1000 room temperature resistance.
R0 = 1000; % Ohm

% IPTS-68 calibration coefficients.
A_IPTS68 = 3.90802E-03;
B_IPTS68 = -5.80195E-07;
C_IPTS68 = -4.27350E-12;

% ITS-90 calibration coefficients.
A_ITS90 = 3.9083E-03;
B_ITS90 = -5.7750E-07;
C_ITS90 = -4.1830E-12;

T_IPTS68 = R2T(A_IPTS68, B_IPTS68, R0, R);
T_ITS90 = R2T(A_ITS90, B_ITS90, R0, R);

figure
plot(R, Tcalib, 'ro',...
     R, T_IPTS68, 'g^',...
     R, T_ITS90, 'bv', 'MarkerSize', 10, 'LineWidth', 2)
title('Resistance Calibration')
xlabel('Resistance (Ohm)')
ylabel('Temperature (K)')
legend('calibration', 'IPTS-68', 'ITS-90', 'Location', 'SouthEast')
axis tight
grid on

figure
plot(R, T_IPTS68 - Tcalib, 'g^',...
     R, T_ITS90 - Tcalib, 'bv', 'MarkerSize', 10, 'LineWidth', 2)
title('Calibration Error')
xlabel('Resistance (Ohm)')
ylabel('Temperature Error (K)')
legend('IPTS-68', 'ITS-90', 'Location', 'SouthEast')
axis tight
grid on
end

function T = R2T(A, B, R0, R)
    T = (-R0 * A + sqrt((R0 * A).^2 - 4 * R0 * B * (R0 - R))) ./...
        (2 * R0 * B) + 273.15;
    % Extra error correction obtained by fitting the error function to
    % the 6th-degree polynomial.
    p1 = 6.0933e-17;
    p2 = -3.2865e-13;
    p3 = 6.8074e-10;
    p4 = -6.8275e-07;
    p5 = 0.00033726;
    p6 = -0.070257;
    p7 = 2.7358;
    T = T - (p1 * R.^6 + p2 * R.^5 + p3 * R.^4 + p4 * R.^3 + p5 * R.^2 +...
             p6 * R + p7);
    % Extra error correction obtaine by fitting the residual error to
    % the 3rd-degree rational funciton.
    a1 = 3.508e+04;
    q1 = -78.44;
    q2 = 2275;
    q3 = -1.855e+04;
    T = T - (a1 ./ (R.^3 + q1 * R.^2 + q2 * R + q3));
end