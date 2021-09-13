# ECE1779A2

First Run getAWSINfo and fill in vpc and subnets info in config 
then 

Run ELBinitializationScript.py once \
get the ouput information and input them in to config. \
This does not need to be done ever again, it ll output duplicate exception 

if somehow sht goes wrong or fails half way through, 
you have to manually configure in aws configure where it failed

Reset by \
delete load balancer \
delete target group \
terminate instance associated with current security groups \
delete security group (remove inbound/outbound rules first) \
then run the script again 

upon success it outputs the information that need to be inputted in the configure file on user basis \

make sure all config info is updated before running the flask