compair = multi_repo.compair()

for puic, imx_compair in compair.values.items():
    print(puic)
    print(imx_compair.global_status)

    for field in imx_compair.fields:
        print(field.name)
        print(field.global_status)

        for value in field.values:
            print(value.container_id)
            print(value.value)
            print(value.status)
