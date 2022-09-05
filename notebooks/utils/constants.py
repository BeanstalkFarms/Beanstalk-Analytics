from box import Box 

ADDR_BEANSTALK = "0xC1E088fC1323b20BCBee9bd1B9fC9546db5624C5".lower()
# names of whitelisted silo tokens 
TOKEN_NAMES_SILO = ['bean', 'bean_3crv', 'ur_bean', 'ur_bean_3crv']
# addresses of whitelisted silo tokens 
ADDR_BEAN = "0xBEA0000029AD1c77D3d5D23Ba2D8893dB9d1Efab".lower()
ADDR_BEAN_3CRV = "0xc9C32cd16Bf7eFB85Ff14e0c8603cc90F6F2eE49".lower()
ADDR_UR_BEAN = "0x1BEA0050E63e05FBb5D8BA2f10cf5800B6224449".lower()
ADDR_UR_BEAN_3CRV = "0x1BEA3CcD22F4EBd3d37d731BA31Eeca95713716D".lower()

# Object for whitelisted silo token addresses 
ADDRS_SILO_TOKENS = Box(dict(
    # tokens 
    bean=ADDR_BEAN,
    bean_3crv=ADDR_BEAN_3CRV,
    ur_bean=ADDR_UR_BEAN, 
    ur_bean_3crv=ADDR_UR_BEAN_3CRV, 
))
# decimal numbers for silo tokens 
DECIMALS_SILO_TOKENS = Box(dict(
    bean=1e6, 
    bean_3crv=1e18, 
    ur_bean=1e6, 
    ur_bean_3crv=1e12, 
))
# Object for all addresses 
ADDRS = Box(dict(
    # contracts 
    beanstalk=ADDR_BEANSTALK, 
    # tokens 
    **ADDRS_SILO_TOKENS,
))
