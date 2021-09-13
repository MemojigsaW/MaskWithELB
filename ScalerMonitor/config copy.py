# ---------------------------------------------------------------------------- #
#            Dynamic Parameters to be changed on user to user basis            #
# ---------------------------------------------------------------------------- #

# -------- GetAWSInfo, Enter Prior to Running ELBinitializaitonScript -------- #
# -------------------------- or get from AWS Console ------------------------- #

VPC_ID = 
VPC_SUBNETS = 
USER_ID = 
PEM_KEY = 

# ------- Information outputed upon success of ELBinitializationScript ------- #
INSTANCE_SECURITY_GROUP=
ELB_SECURITY_GROUP=
TARGET_GROUP_ARN=
ELB_ARN=
ELB_DNS=
LIS_ARN=
# --------------------- Instance S3, IAM, and RDS configs -------------------- #
AMI_USED = 
IAM_ROLE_NAME = 
USER_DATA =

db_config = 
BUCKET_NAME =


# -------------------- End of User basis info -------------------------- #


# ---------------------------------------------------------------------------- #
#                               Static Parameters                              #
# ---------------------------------------------------------------------------- #
# ------------------------------- Do not change ------------------------------ #

#Instance Security Groups
ISG_DESCRIPTION = 
ISG_NAME =

#Loader Security Groups
LSG_DESCRIPTION = 
LSG_NAME = 

#ELB info
ELB_NAME = 

#Instance Info
INSTANCE_TYPE = 
FLASK_PORT = 
INSERVICE_BLOCK_INTERVAL = 
INSERVICE_BLOCK_ATTEMPTS = 

#Flask Info
SECRET_KEY = 