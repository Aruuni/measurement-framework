while true;
do
    # ‘s/regexp/replacement/flags’
    # -E: use normal RegEx syntax 
    # -e#1: BBR v2 with pacing_gain and cwnd_gain being optional
    # -e#2: BBR v1
    # -e#3: Cubic
    # ts: add timestamp 
    ./ss -tin | sed -En \
        -e 's/.* cwnd:([0-9]*).* bbr:\((.*mrtt:[0-9.]*.*),(bw_hi:[^)]*).*/\1;;\2;\3;/p' \
        -e 's/.* cwnd:([0-9]*).* bbr:\(([^)]*)\).*/\1;;\2/p' \
        -e 's/.* cwnd:([0-9]*).* ssthresh:([0-9]*).*/\1;\2;/p' \
        | ts '%.s;'
    sleep $1; 
done 