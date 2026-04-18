{% macro input_path(file_path) %}
    {{ return(var('input_data_base_path') ~ '\\' ~ file_path) }}
{% endmacro %}

{% macro output_path(file_path) %}
    {{ return(var('output_data_base_path') ~ '\\' ~ file_path) }}
{% endmacro %}