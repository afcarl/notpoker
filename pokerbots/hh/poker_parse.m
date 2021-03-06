dirname = 'C:\Documents and Settings\vivek\My Documents\code\notpoker\pokerbots\hh\';

file_list = dir(dirname);
badfiles=[];
for i=1:length(file_list)
    if length(file_list(i).name)<4 || ~strcmp(file_list(i).name(end-3:end),'.txt')
        badfiles=[badfiles i];
    end
end
file_list(badfiles)=[];

for i = 1:length(file_list)
    
    the_file = [dirname file_list(i).name];   
    fid = fopen(the_file);
    score = zeros(0,2);
    while 1
        s = fgetl(fid);
        if ~ischar(s)
            break
        elseif findstr(s,'Seat 1:')
            par_open = findstr(s,'(');
            par_close = findstr(s,')');
            score1 = str2double(s(par_open(end)+1:par_close(end)-1));
            t = fgetl(fid);
            par_open = findstr(t,'(');
            par_close = findstr(t,')');
            score2 = str2double(t(par_open(end)+1:par_close(end)-1));
            score = [score; score1 score2];
        end
    end
    fclose(fid);
    
    figure(1);
    clf;
    hold on;
    plot(score(:,1),'b');
    plot(score(:,2),'r');
    legend('n00b','Master Chef',2);
    xlabel('Hands');
    
    if score(end,2) > score(end,1)
        winner_array(i) = 1;
    end
    num_hands(i) = size(score,1);

    pause(0.01);
    
end

avg_win = 100*mean(winner_array)
std_win = 100*sqrt(mean(winner_array)*(1-mean(winner_array))/length(winner_array))
avg_hands = mean(num_hands)

