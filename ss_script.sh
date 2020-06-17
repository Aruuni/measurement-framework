while true;
do
    # ‘s/regexp/replacement/flags’
    # -E: use normal RegEx syntax 
    # tr: remove newlines
    # sed #2: reorder output - very ugly, but the only solution I found
    # ts: add timestamp 
    strace ss -tin 2>&1 | sed -En \
        -e 's/.* cwnd:([0-9]*).* bbr:\(([^)]*)\).*/\1;;\2;/p' \
        -e 's/.* \{(bbr_bw_lo=[^,]*),\s(bbr_bw_hi=[^,]*).*/\1,\2;/p' \
        -e 's/.* cwnd:([0-9]*).* ssthresh:([0-9]*).*/\1;\2;/p' \
        | tr -d '\n' \
        | sed -En -e 's/(bbr_bw_lo=[^,]*,bbr_bw_hi=[^;]*;)(.*)/\2\1\n/p' \
        | ts '%.s;'
    sleep $1; 
done 